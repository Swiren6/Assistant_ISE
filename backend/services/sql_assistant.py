import os
import json
from typing import List, Dict, Tuple
from pathlib import Path

# Charger les variables d'environnement
from dotenv import load_dotenv

# Charger le fichier .env
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"🔧 SQLAssistant: .env chargé depuis {env_path}")
else:
    print(f"⚠️ SQLAssistant: .env non trouvé à {env_path}")

# Import conditionnel pour les dépendances optionnelles
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("⚠️ MySQL connector non disponible")

try:
    import tiktoken 
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("⚠️ Tiktoken non disponible")

class SQLAssistant:
    def __init__(self):
        # Vérification des variables d'environnement
        print("🔍 SQLAssistant - Variables d'environnement:")
        print(f"  MYSQL_HOST: {os.getenv('MYSQL_HOST', 'NON DÉFINIE')}")
        print(f"  MYSQL_USER: {os.getenv('MYSQL_USER', 'NON DÉFINIE')}")
        print(f"  MYSQL_DATABASE: {os.getenv('MYSQL_DATABASE', 'NON DÉFINIE')}")
        print(f"  MYSQL_PASSWORD: {'***' if os.getenv('MYSQL_PASSWORD') else 'NON DÉFINIE'}")
        
        # Configuration MySQL depuis les variables d'environnement
        # Configuration MySQL depuis les variables d'environnement
        self.mysql_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', '3306')),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', 'root'),
            'database': os.getenv('MYSQL_DATABASE', 'bd_eduise2'),
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': True
        }
        
        # Test de connexion MySQL (optionnel)
        self.mysql_connected = False
        if MYSQL_AVAILABLE:
            try:
                conn = mysql.connector.connect(**self.mysql_config)
                conn.close()
                self.mysql_connected = True
                print("✅ Connexion MySQL réussie.")
            except Exception as e:
                print(f"⚠️ MySQL non connecté: {e}")
                print("💡 Mode démo activé - réponses simulées")
        
        # Initialisation du tokenizer (optionnel)
        self.enc = None
        if TIKTOKEN_AVAILABLE:
            try:
                self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
                print("✅ Tokenizer initialisé")
            except Exception as e:
                print(f"⚠️ Erreur tokenizer: {e}")
        
        # Initialisation du cache
        self.cache_file_path = os.path.join(os.path.dirname(__file__), "..", "question_cache2.json")
        self.cache_data = self.load_cache()
        
        # Données de démonstration
        self.demo_data = {
            "combien d'élèves": "Il y a actuellement 1,247 élèves dans le système.",
            "nombre d'élèves": "Total des élèves: 1,247",
            "élèves par classe": """Classes et effectifs:
6ème A: 28 élèves
6ème B: 30 élèves  
5ème A: 25 élèves
5ème B: 27 élèves
4ème A: 24 élèves
3ème A: 26 élèves""",
            "localités": """Localités disponibles:
- Tunis: 450 élèves
- Sfax: 320 élèves
- Sousse: 280 élèves
- Kairouan: 197 élèves""",
            "délégations": """Délégations:
- Tunis Centre: 150 élèves
- Tunis Nord: 180 élèves
- Tunis Sud: 120 élèves
- Sfax Ville: 200 élèves
- Sfax Sud: 120 élèves"""
        }

    def ask_llm(self, prompt: str) -> str:
        """Simulation d'un LLM pour générer du SQL"""
        # Mapping simple question -> SQL
        sql_mapping = {
            "combien": "SELECT COUNT(*) as total FROM eleve;",
            "nombre": "SELECT COUNT(*) as total FROM eleve;",
            "élèves": "SELECT COUNT(*) as total FROM eleve;",
            "classe": "SELECT classe, COUNT(*) as effectif FROM eleve GROUP BY classe;",
            "localité": "SELECT l.nom, COUNT(e.id) as nb_eleves FROM localite l LEFT JOIN eleve e ON e.localite_id = l.id GROUP BY l.nom;",
            "délégation": "SELECT d.nom, COUNT(e.id) as nb_eleves FROM delegation d LEFT JOIN eleve e ON e.delegation_id = d.id GROUP BY d.nom;"
        }
        
        prompt_lower = prompt.lower()
        for keyword, sql in sql_mapping.items():
            if keyword in prompt_lower:
                return sql
        
        # SQL par défaut
        return "SELECT COUNT(*) as total FROM eleve;"

    def count_tokens(self, text: str) -> int:
        """Compte les tokens pour un texte donné"""
        if self.enc:
            return len(self.enc.encode(text))
        else:
            # Approximation simple
            return len(text.split()) * 1.3

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> Tuple[int, float]:
        """Calcule le coût total"""
        total_tokens = prompt_tokens + completion_tokens
        # Coûts simulés
        total_cost = total_tokens * 0.0001  # 0.01 centime par token
        return int(total_tokens), round(total_cost, 6)

    def execute_sql_real(self, query: str) -> str:
        """Exécute une requête SQL réelle"""
        if not self.mysql_connected or not MYSQL_AVAILABLE:
            return None
            
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            cursor = conn.cursor()
            
            cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                if results:
                    # Format simple pour l'affichage
                    formatted_result = f"{' | '.join(columns)}\n"
                    formatted_result += "-" * (len(' | '.join(columns))) + "\n"
                    
                    for row in results[:20]:  # Limite à 20 résultats
                        formatted_result += f"{' | '.join(map(str, row))}\n"
                    
                    return formatted_result
                else:
                    return "Aucun résultat trouvé."
            else:
                conn.commit()
                return f"Requête exécutée avec succès. {cursor.rowcount} ligne(s) affectée(s)."
                
        except Exception as e:
            return f"Erreur SQL: {str(e)}"
        finally:
            if 'conn' in locals():
                conn.close()

    def execute_sql_demo(self, query: str, question: str) -> str:
        """Simule l'exécution SQL avec des données de démonstration"""
        question_lower = question.lower()
        
        # Recherche dans les données de démo
        for keyword, response in self.demo_data.items():
            if any(word in question_lower for word in keyword.split()):
                return response
        
        # Réponse par défaut basée sur le type de requête
        if "count" in query.lower():
            return "total\n-----\n1247"
        elif "group by" in query.lower():
            return """classe | effectif
------|---------
6ème A | 28
5ème A | 25
4ème A | 24
3ème A | 26"""
        else:
            return "Données de démonstration non disponibles pour cette requête."

    def ask_question(self, question: str) -> Tuple[str, str, float, int]:
        """Traite une question et retourne la réponse"""
        # Vérifier le cache
        if question in self.cache_data:
            cached = self.cache_data[question]
            print("💡 Réponse chargée depuis le cache")
            return cached["sql"], cached["response"], 0.0, 0
        
        try:
            # Prompt simple pour générer du SQL
            prompt = f"""
            Question: {question}
            
            Génère une requête SQL MySQL appropriée.
            Tables disponibles: eleve, personne, localite, delegation
            """
            
            # Génération de la requête SQL
            sql_query = self.ask_llm(prompt).strip()
            print(f"🔍 Requête générée: {sql_query}")

            # Tentative d'exécution réelle
            result = self.execute_sql_real(sql_query)
            
            # Si pas de base de données, utiliser les données de démo
            if result is None:
                result = self.execute_sql_demo(sql_query, question)
                print("🎭 Mode démonstration activé")
            
            print(f"⚡ Résultat: {result}")
            
            # Calcul des tokens et coûts
            prompt_tokens = self.count_tokens(prompt)
            completion_tokens = self.count_tokens(sql_query)
            total_tokens, total_cost = self.calculate_cost(prompt_tokens, completion_tokens)
            
            # Format de la réponse
            if result and not result.startswith("Erreur"):
                formatted_response = f"Réponse à: {question}\n\n{result}"
                
                # Mise en cache
                self.cache_data[question] = {
                    "sql": sql_query,
                    "response": formatted_response
                }
                self.save_cache()
                
                return sql_query, formatted_response, total_cost, total_tokens
            else:
                return sql_query, result or "Aucune donnée trouvée", total_cost, total_tokens
                
        except Exception as e:
            error_msg = f"❌ Erreur: {str(e)}"
            print(error_msg)
            return "", error_msg, 0.0, 0

    def load_cache(self) -> dict:
        """Charge le cache depuis le fichier"""
        try:
            if os.path.exists(self.cache_file_path):
                with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"⚠️ Erreur de chargement du cache: {e}")
            return {}

    def save_cache(self):
        """Sauvegarde le cache"""
        try:
            os.makedirs(os.path.dirname(self.cache_file_path), exist_ok=True)
            with open(self.cache_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
            print("✅ Cache sauvegardé")
        except Exception as e:
            print(f"❌ Erreur de sauvegarde du cache: {e}")

    def get_status(self) -> dict:
        """Retourne le statut de tous les composants"""
        return {
            "mysql_available": MYSQL_AVAILABLE,
            "mysql_connected": self.mysql_connected,
            "tiktoken_available": TIKTOKEN_AVAILABLE,
            "demo_mode": not self.mysql_connected,
            "cache_entries": len(self.cache_data)
        }

# Test rapide si exécuté directement
if __name__ == "__main__":
    assistant = SQLAssistant()
    print(f"Status: {assistant.get_status()}")
    
    # Test simple
    sql, response, cost, tokens = assistant.ask_question("Combien d'élèves dans le système?")
    print(f"SQL: {sql}")
    print(f"Réponse: {response}")
    print(f"Tokens: {tokens}, Coût: ${cost}")