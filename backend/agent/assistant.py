from typing import List, Dict, Optional, Any
import json
import re
from pathlib import Path
from config.database import get_db
from langchain.prompts import PromptTemplate

from agent.cache_manager import CacheManager
from agent.llm_utils import ask_llm 
from agent.template_matcher.matcher import SemanticTemplateMatcher
import logging
logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """
[SYSTEM] Vous êtes un assistant SQL expert pour une base de données scolaire.
Votre rôle est de traduire des questions en français en requêtes SQL MySQL.

ATTENTION PARTICULIÈRE POUR LES QUESTIONS DE COMPTAGE:
**Pour "nombre d'élèves" ou "combien d'élèves", utilisez: SELECT COUNT(*) AS nombre_eleves FROM eleve
**Pour "nombre d'élèves inscrits cette année", utilisez: 
   SELECT COUNT(*) AS nombre_eleves 
   FROM eleve e 
   JOIN inscriptioneleve ie ON e.id = ie.Eleve 
   WHERE ie.Annuler = 0 AND ie.AnneeScolaire = (SELECT id FROM anneescolaire WHERE AnneeScolaire LIKE '%2024%')

RÈGLES GÉNÉRALES:
**l'année scolaire se trouve dans anneescolaire.AnneeScolaire non pas dans Annee 
**si on dit l'année XXXX/YYYY on parle de l'année scolaire XXXX/YYYY 
**les table eleve et parent ne contiennent pas les noms et les prénoms. ils se trouvent dans la table personne.
**les colonnes principales du table personne sont : id, NomFr, PrenomFr, NomAr, PrenomAr, Cin, AdresseFr, AdresseAr, Tel1, Tel2, Nationalite, Localite, Civilite.
**utilisez des JOINs explicites plutôt que des sous-requêtes quand c'est possible.
**pour les requêtes de comptage, utilisez toujours un alias descriptif comme "nombre_eleves", "total_classes", etc.

Voici la structure détaillée des tables pertinentes pour votre tâche :
{table_info}

---
**Description des domaines pertinents pour cette question :**
{relevant_domain_descriptions}

---
**Informations Clés et Relations :**
{relations}

---
**INSTRUCTIONS CRUCIALES :**
1. Répondez UNIQUEMENT par une requête SQL MySQL valide et correcte.
2. Ne mettez AUCUN texte explicatif ou commentaire avant ou après la requête SQL.
3. Générez des requêtes SELECT uniquement.
4. Pour les questions de comptage, utilisez COUNT(*) avec un alias descriptif en français.
5. Si la question demande "combien" ou "nombre de", c'est forcément une requête COUNT.

Question : {user_question}
Requête SQL :
"""
class SQLAssistant:
    def __init__(self):
        self.db = get_db()
        self.connection = None 
        self.relations_description = self.load_relations()
        self.domain_descriptions = self.load_domain_descriptions()
        self.domain_to_tables_mapping = self.load_domain_to_tables_mapping()
        self.ask_llm = ask_llm
        self.cache = CacheManager()
        self.template_matcher = SemanticTemplateMatcher()

        try:
            self.templates_questions = self.load_question_templates()
            if self.templates_questions:
                print(f"✅ {len(self.templates_questions)} templates chargés")
                self.template_matcher.load_templates(self.templates_questions)
            else:
                print("⚠️ Aucun template valide - fonctionnement en mode LLM seul")
        except ValueError as e:
            print(f"❌ Erreur de chargement des templates: {str(e)}")
            self.templates_questions = []
        self.clear_cache()

    def get_table_info(self):
        """Get information about database tables using Flask-MySQLdb"""
        try:
            # Créer une nouvelle connexion pour chaque opération
            cur = self.db.connection.cursor()
            
            # Get tables
            cur.execute("SHOW TABLES")
            tables = cur.fetchall()
            
            table_info = {}
            
            for table in tables:
                # Gérer les deux formats possibles de retour
                table_name = table[0] if isinstance(table, tuple) else list(table.values())[0]
                
                # Get columns
                cur.execute(f"DESCRIBE {table_name}")
                columns = cur.fetchall()
                
                table_info[table_name] = {
                    'columns': columns,
                    'primary_key': [col['Field'] if isinstance(col, dict) else col[0] 
                                for col in columns if (col.get('Key') == 'PRI' if isinstance(col, dict) else col[3] == 'PRI')]
                }
            
            cur.close()
            return json.dumps(table_info, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error getting table info: {str(e)}")
            raise

    def run_query(self, sql_query):
        """Execute a SQL query using Flask-MySQLdb"""
        cur = None
        try:
            # Créer une nouvelle connexion pour chaque requête
            cur = self.db.connection.cursor()
            cur.execute(sql_query)
            
            if sql_query.strip().upper().startswith('SELECT'):
                result = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                return {'columns': columns, 'rows': result}
            else:
                self.db.connection.commit()
                return {'affected_rows': cur.rowcount}
        except Exception as e:
            if hasattr(self.db, 'connection'):
                try:
                    self.db.connection.rollback()
                except:
                    pass
            raise e
        finally:
            if cur:
                cur.close()
    def load_question_templates(self) -> list:
        base_path = Path(__file__).parent
        file_path = base_path / 'templates_questions.json'
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('questions', [])
        except FileNotFoundError:
            print(f"⚠️ Fichier {file_path} non trouvé. Création d'un fichier vide.")
            Path(file_path).touch()
            return []
        except Exception as e:
            print(f"❌ Erreur lors du chargement des templates: {e}")
            return []

    def find_matching_template(self, question: str) -> Optional[Dict[str, Any]]:
        exact_match = self._find_exact_template_match(question)
        if exact_match:
            return exact_match

        semantic_match, score = self.template_matcher.find_similar_template(question)
        if semantic_match:
            print(f"🔍 Template sémantiquement similaire trouvé (score: {score:.2f})")
            return self._extract_variables(question, semantic_match)

        return None

    def _find_exact_template_match(self, question: str) -> Optional[Dict[str, Any]]:
        cleaned_question = question.rstrip(' ?')
        for template in self.templates_questions:
            pattern = template["template_question"]
            regex_pattern = re.sub(r'\{(.+?)\}', r'(?P<\1>.+?)', pattern)
            match = re.fullmatch(regex_pattern, cleaned_question, re.IGNORECASE)
            if match:
                variables = {k: v.strip() for k, v in match.groupdict().items()}
                return {
                    "template": template,
                    "variables": variables if variables else {}
                }
        return None

    def _extract_variables(self, question: str, template: Dict) -> Dict[str, Any]:
        template_text = template["template_question"]
        variables = {}

        annee_pattern = r"(20\d{2}[-\/]20\d{2})"
        annee_match = re.search(annee_pattern, question)
        if annee_match:
            variables["AnneeScolaire"] = annee_match.group(1).replace("-", "/")

        var_names = re.findall(r'\{(.+?)\}', template_text)
        for var_name in var_names:
            if var_name not in variables:
                keyword_pattern = re.escape(template_text.split(f"{{{var_name}}}")[0].split()[-1])
                pattern = fr"{keyword_pattern}\s+([^\s]+)"
                match = re.search(pattern, question, re.IGNORECASE)
                if match:
                    variables[var_name] = match.group(1).strip(",.?!")

        return {
            "template": template,
            "variables": variables if variables else {}
        }

    def generate_query_from_template(self, template: Dict, variables: Dict) -> str:
        requete = template["requete_template"]
        if not variables:
            return requete

        for var_name, var_value in variables.items():
            clean_value = str(var_value).split('?')[0].strip(",.!?\"'")

            if var_name.lower() == "anneescolaire":
                clean_value = clean_value.replace("-", "/")

            requete = requete.replace(f'{{{var_name}}}', clean_value)

        return requete

    def load_domain_descriptions(self) -> dict:
        base_path = Path(__file__).parent
        file_path = base_path / 'prompts' / 'domain_descriptions.json'
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_relations(self) -> str:
        base_path = Path(__file__).parent
        file_path = base_path / 'prompts' / 'relations.txt'
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_domain_to_tables_mapping(self) -> dict:
        base_path = Path(__file__).parent
        file_path = base_path / 'prompts' / 'domain_tables_mapping.json'
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_relevant_domains(self, query: str, domain_descriptions: Dict[str, str]) -> List[str]:
        domain_desc_str = "\n".join([f"- {name}: {desc}" for name, desc in domain_descriptions.items()])
        domain_prompt_content = f"""
        Based on the following user question, identify ALL relevant domains from the list below.
        Return only the names of the relevant domains, separated by commas. If no domain is relevant, return 'None'.

        User Question: {query}

        Available Domains and Descriptions:
        {domain_desc_str}

        Relevant Domains (comma-separated):
        """

        try:
            response = self.ask_llm(domain_prompt_content)
            domain_names = response.strip()

            if domain_names.lower() == 'none' or not domain_names:
                return []
            return [d.strip() for d in domain_names.split(',')]
        except Exception as e:
            print(f"❌ Erreur lors de l'identification des domaines: {e}")
            return []

    def get_tables_from_domains(self, domains: List[str], domain_to_tables_map: Dict[str, List[str]]) -> List[str]:
        tables = []
        for domain in domains:
            tables.extend(domain_to_tables_map.get(domain, []))
        return sorted(list(set(tables)))

    def ask_question(self, question: str) -> tuple[str, str]:
        logger.info(f"📨 Question reçue: {question}")

        # Vérifier le cache
        cached = self.cache.get_cached_query(question)
        if cached:
            sql_template, variables = cached
            sql_query = sql_template
            for column, value in variables.items():
                sql_query = sql_query.replace(f"{{{column}}}", value)

            logger.info("♻️ Requête récupérée depuis le cache")
            print(f"⚡ SQL depuis cache: {sql_query}")

            try:
                result = self.run_query(sql_query)
                formatted = self.format_result(result, question)
                logger.info("✅ Requête exécutée depuis le cache avec succès")
                return sql_query, formatted
            except Exception as db_error:
                logger.error(f"❌ Erreur SQL (cache): {db_error}")
                return sql_query, f"❌ Erreur d'exécution SQL : {str(db_error)}"

        # Essayer de matcher un template
        template_match = self.find_matching_template(question)
        if template_match:
            logger.info("📋 Template reconnu pour la question")
            print("🔍 Template trouvé")

            sql_query = self.generate_query_from_template(
                template_match["template"],
                template_match["variables"]
            )
            print(f"⚙️ SQL générée via template: {sql_query}")
            logger.info(f"⚙️ SQL via template: {sql_query}")

            try:
                result = self.run_query(sql_query)
                formatted = self.format_result(result, question)
                self.cache.cache_query(question, sql_query)
                logger.info("✅ Requête exécutée depuis template avec succès")
                return sql_query, formatted
            except Exception as db_error:
                logger.error(f"❌ Erreur SQL (template): {db_error}")
                return sql_query, f"❌ Erreur d'exécution SQL : {str(db_error)}"

        # Sinon, fallback vers le LLM
        logger.info("🤖 Aucun template trouvé, fallback vers LLM")
        print("🔍 Aucun template trouvé → Génération LLM")

        prompt = PROMPT_TEMPLATE.format(
            user_question=question,
            table_info=self.get_table_info(),
            relevant_domain_descriptions="\n".join(self.domain_descriptions.values()),
            relations=self.relations_description
        )

        
        sql_query = self.ask_llm(prompt)
        if not sql_query:
            logger.warning("🚨 Requête vide générée par le LLM")
            return "", "❌ La requête générée est vide."

        sql_query = sql_query.strip()
        logger.info(f"🧠 SQL générée par LLM: {sql_query}")
        print(f"🧠 SQL LLM: {sql_query}")

        try:
            result = self.run_query(sql_query)
            formatted = self.format_result(result, question)
            self.cache.cache_query(question, sql_query)
            logger.info("✅ Requête exécutée avec succès depuis le LLM")
            return sql_query, formatted
        except Exception as db_error:
            logger.error(f"❌ Erreur SQL (LLM): {db_error}")
            return sql_query, f"❌ Erreur d'exécution SQL : {str(db_error)}"
    
    def format_result(self, result: dict, question: str = "") -> str:
        """Format the query results for display"""
        if not result or 'rows' not in result or not result['rows']:
            return "✅ Requête exécutée mais aucun résultat trouvé."

        try:
            rows = result['rows']
            columns = result['columns']
            
            # Cas spécial pour les requêtes COUNT
            if len(columns) == 1 and len(rows) == 1:
                col_name = columns[0].lower()
                value = list(rows[0].values())[0] if isinstance(rows[0], dict) else rows[0][0]
                
                # Détection des questions de comptage
                if self.is_count_question(question):
                    if 'élève' in question.lower() or 'eleve' in question.lower():
                        return f"Le nombre d'élèves est de **{value}** élèves."
                    elif 'classe' in question.lower():
                        return f"Le nombre de classes est de **{value}** classes."
                    elif 'enseignant' in question.lower() or 'professeur' in question.lower():
                        return f"Le nombre d'enseignants est de **{value}** enseignants."
                    elif 'parent' in question.lower():
                        return f"Le nombre de parents est de **{value}** parents."
                    else:
                        return f"Le résultat du comptage est de **{value}**."
                
                # Si c'est clairement une colonne COUNT
                if 'count' in col_name or col_name.startswith('nombre'):
                    return f"Le résultat est : **{value}**"
            
            # Format tableau pour les autres résultats
            formatted = []
            if question:
                formatted.append(f"**Résultats pour :** {question}\n")

            # Format headers
            header_line = " | ".join(columns)
            formatted.append(header_line)

            # Format separator
            separator = "-+-".join(['-' * max(len(h), 4) for h in columns])
            formatted.append(separator)

            # Format rows (limiter à 10 premières lignes pour éviter les réponses trop longues)
            row_count = 0
            for row in rows:
                if row_count >= 10:
                    formatted.append(f"... et {len(rows) - 10} autres résultats")
                    break
                
                if isinstance(row, dict):
                    formatted.append(" | ".join(str(value) if value is not None else 'NULL' for value in row.values()))
                else:
                    formatted.append(" | ".join(str(value) if value is not None else 'NULL' for value in row))
                row_count += 1

            return "\n".join(formatted)
            
        except Exception as e:
            logger.error(f"Erreur formatage: {e}")
            return f"❌ Erreur de formatage: {str(e)}"
         
    def clear_cache(self):
        """Vider le cache pour éviter les mauvaises requêtes"""
        if hasattr(self.cache, 'clear'):
            self.cache.clear()
        logger.info("🗑️ Cache vidé")
    
    def is_count_question(self, question: str) -> bool:
        """Détecte si la question demande un comptage"""
        count_keywords = [
            'nombre', 'combien', 'count', 'total', 
            'quantité', 'effectif', 'dénombr'
        ]
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in count_keywords)