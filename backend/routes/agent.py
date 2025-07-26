from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
import logging
import traceback
from config.database import init_db, get_db,get_db_connection


agent_bp = Blueprint('agent_bp', __name__)
logger = logging.getLogger(__name__)

# Initialisation assistant
assistant = None
try:
    from agent.assistant import SQLAssistant
    from config.database import get_db

    assistant = SQLAssistant(db=get_db())


    if assistant and assistant.db:
        print("✅ Connexion DB disponible dans assistant")
    else:
        print("❌ Connexion DB manquante dans assistant")

    print("✅ Assistant chargé avec succès")
except Exception as e:
    print(f"❌ Erreur assistant: {e}")
    assistant = None

@agent_bp.route('/ask', methods=['POST'])
def ask_sql():  # 🔧 Supprimé @jwt_required temporairement
    print("🔥🔥🔥 VERSION SANS JWT_REQUIRED 🔥🔥🔥")
    print("=== NOUVELLE REQUÊTE /ask ===")
    
    # 🔧 Gestion JWT manuelle et optionnelle
    jwt_valid = False
    current_user = None
    
    try:
        # Essayer de vérifier le JWT si présent
        if 'Authorization' in request.headers:
            print("🔑 Token JWT détecté, vérification...")
            verify_jwt_in_request(optional=True)
            current_user = get_jwt_identity()
            jwt_valid = True
            print(f"✅ JWT valide pour utilisateur: {current_user}")
        else:
            print("ℹ️ Pas de token JWT, accès anonyme")
    except Exception as jwt_error:
        print(f"⚠️ Erreur JWT (ignorée): {jwt_error}")
        # On continue sans JWT
    
    try:
        # Validation JSON
        if not request.is_json:
            print("❌ Pas de JSON")
            return jsonify({"error": "JSON requis"}), 415
        
        # Récupération données
        data = request.get_json()
        print(f"🔍 Données reçues: {data}")
        print(f"🔍 Utilisateur: {current_user if jwt_valid else 'Anonyme'}")
        
        if not data:
            print("❌ Données vides")
            return jsonify({"error": "Pas de données"}), 400
        
        # Recherche de la question
        question = None
        field_found = None
        
        possible_fields = ['question', 'subject', 'query', 'text', 'message', 'prompt']
        for field in possible_fields:
            if field in data:
                value = data[field]
                print(f"🔍 Champ '{field}' trouvé: {value} (type: {type(value)})")
                if value and str(value).strip():
                    question = str(value).strip()
                    field_found = field
                    break
        
        print(f"🎯 Question finale: '{question}' (depuis champ: {field_found})")
        
        if not question:
            print("❌ Aucune question trouvée")
            return jsonify({
                "error": "Question manquante",
                "received_fields": list(data.keys()),
                "msg": "Aucune question valide trouvée"
            }), 422
        
        # Vérification assistant
        if not assistant:
            print("❌ Assistant indisponible")
            return jsonify({"error": "Assistant indisponible"}), 503
        
        print(f"🚀 Traitement: '{question}'")
        
        # Traitement    
        try:
            sql_query, response = assistant.ask_question(question)
            print(f"✅ Succès: SQL={sql_query}")
            
            result = {
                "sql_query": sql_query,
                "response": response,
                "status": "success"
            }
            
            # Ajouter info utilisateur si JWT valide
            if jwt_valid:
                result["user"] = current_user
            
            return jsonify(result), 200
            
        except Exception as e:
            print(f"❌ Erreur traitement: {e}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return jsonify({
                "error": "Erreur traitement",
                "msg": str(e)
            }), 500
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": "Erreur serveur",
            "msg": str(e)
        }), 500
        
@agent_bp.route('/ask', methods=['GET'])
def ask_info():
    """Information sur l'endpoint"""
    return jsonify({
        "message": "Assistant IA pour questions scolaires",
        "method": "POST",
        "format": {"question": "Votre question ici"},
        "status": "OK" if assistant else "ERROR"
    })

@agent_bp.route('/health', methods=['GET'])
def health():
    """Vérification de santé"""
    return jsonify({
        "status": "OK",
        "assistant": "OK" if assistant else "ERROR"
    })