# # from flask import Blueprint, request, jsonify
# # from agent.assistant import SQLAssistant
# # from flask_jwt_extended import jwt_required  # facultatif si tu veux protéger l'accès
# # import logging

# # assistant = SQLAssistant()
# # agent_bp = Blueprint('agent_bp', __name__)
# # logger = logging.getLogger(__name__)

# # @agent_bp.route('/ask', methods=['POST'])
# # @jwt_required(optional=True)
# # def ask_sql():
# #     # Vérification du Content-Type
# #     if not request.is_json:
# #         return jsonify({"error": "Content-Type must be application/json"}), 415
    
# #     try:
# #         data = request.get_json()
# #         if not data:
# #             return jsonify({"error": "No JSON data received"}), 400
            
# #         # Validation du champ 'question'
# #         if 'question' not in data or not isinstance(data['question'], str):
# #             return jsonify({"error": "Question must be a non-empty string"}), 422
            
# #         question = data['question'].strip()
# #         if not question:
# #             return jsonify({"error": "Question cannot be empty"}), 422

# #         # Logging pour débogage
# #         current_app.logger.info(f"Question reçue : {question}")
        
# #         try:
# #             sql_query, response = assistant.ask_question(question)
# #             return jsonify({
# #                 "sql_query": sql_query,
# #                 "response": response
# #             })
# #         except Exception as e:
# #             current_app.logger.error(f"Erreur de traitement : {str(e)}")
# #             return jsonify({"error": "Failed to process question"}), 500
            
# #     except Exception as e:
# #         current_app.logger.error(f"Erreur JSON : {str(e)}")
# #         return jsonify({"error": "Invalid request format"}), 400

# # @agent_bp.route('/ask', methods=['GET'])
# # def ask_info():
# #     return jsonify({"message": "Agent IA prêt à recevoir les questions 📚🧠"}), 200


# from flask import Blueprint, request, jsonify, current_app
# from flask_jwt_extended import jwt_required
# import logging

# # Import de l'assistant - à compléter selon votre structure
# from agent.assistant import SQLAssistant

# agent_bp = Blueprint('agent_bp', __name__)
# logger = logging.getLogger(__name__)

# assistant = SQLAssistant()  #


# @agent_bp.route('/ask', methods=['POST'])
# @jwt_required(optional=True)
# def ask_sql():
#     """Endpoint pour traiter les questions du chat"""
#     current_app.logger.info("=== Nouvelle requête /ask ===")
    
#     # Vérification du Content-Type
#     if not request.is_json:
#         return jsonify({"error": "Content-Type must be application/json"}), 415
    
#     try:
#         data = request.get_json()
#         current_app.logger.info(f"Données reçues: {data}")
        
#         if not data:
#             return jsonify({"error": "No JSON data received"}), 400
            
#         # Validation améliorée
#         question = data.get('question')
#         if question is None:
#             return jsonify({"error": "Missing 'question' field"}), 422
            
#         if not isinstance(question, str):
#             return jsonify({"error": "Question must be a string"}), 422
            
#         question = question.strip()
#         if not question:
#             return jsonify({"error": "Question cannot be empty"}), 422

#         # Traitement normal...
#         try:
#             sql_query, response = assistant.ask_question(question)
#         except Exception as e:
#             current_app.logger.error(f"Erreur assistant: {str(e)}")
#             return jsonify({"error": "Erreur dans la génération de la réponse"}), 500
#         response = f"Réponse à: {question}"
        
#         return jsonify({
#             "sql_query": sql_query,
#             "response": response
#         }), 200
        
#     except Exception as e:
#         current_app.logger.error(f"Erreur: {str(e)}")
#         return jsonify({"error": "Server error"}), 500@agent_bp.route('/ask', methods=['GET'])
# def ask_info():
#     """Information sur l'endpoint ask"""
#     return jsonify({
#         "message": "Agent IA prêt à recevoir les questions 📚🧠",
#         "endpoint": "/api/ask",
#         "method": "POST",
#         "required_fields": ["question"],
#         "example": {
#             "question": "Combien d'élèves sont inscrits cette année?"
#         }
#     }), 200

# @agent_bp.route('/test', methods=['GET'])
# def test_agent():
#     """Test simple de l'agent"""
#     return jsonify({
#         "status": "Agent endpoint working",
#         "timestamp": "2024-01-01 12:00:00"
#     }), 200 

    
    


from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
import logging
import traceback

agent_bp = Blueprint('agent_bp', __name__)
logger = logging.getLogger(__name__)

# Initialisation sécurisée de l'assistant
assistant = None
try:
    from agent.assistant import SQLAssistant
    assistant = SQLAssistant()
    logger.info("✅ SQLAssistant initialisé avec succès")
    print("✅ SQLAssistant initialisé avec succès")
except Exception as e:
    logger.error(f"❌ Erreur d'initialisation SQLAssistant: {e}")
    print(f"❌ Erreur d'initialisation SQLAssistant: {e}")
    assistant = None

@agent_bp.route('/ask', methods=['POST'])
@jwt_required(optional=True)
def ask_sql():
    """Endpoint pour traiter les questions du chat"""
    current_app.logger.info("=== NOUVELLE REQUÊTE /ask ===")
    print("=== NOUVELLE REQUÊTE /ask ===")
    
    # Log des headers pour debugging
    print(f"Headers reçus: {dict(request.headers)}")
    print(f"Content-Type: {request.content_type}")
    print(f"Is JSON: {request.is_json}")
    
    # Vérification du Content-Type
    if not request.is_json:
        error_msg = "Content-Type must be application/json"
        print(f"❌ {error_msg}")
        return jsonify({"error": error_msg, "msg": error_msg}), 415
    
    try:
        # Récupération des données
        data = request.get_json()
        print(f"🔍 Données JSON reçues: {data}")
        current_app.logger.info(f"Données reçues: {data}")
        
        if not data:
            error_msg = "No JSON data received"
            print(f"❌ {error_msg}")
            return jsonify({"error": error_msg, "msg": error_msg}), 400
        
        # VALIDATION FLEXIBLE - accepter question OU subject
        question = None
        if 'question' in data:
            question = data['question']
            print(f"✅ Champ 'question' trouvé: {question}")
        elif 'subject' in data:
            question = data['subject']
            print(f"✅ Champ 'subject' trouvé (converti en question): {question}")
        else:
            error_msg = "Missing 'question' or 'subject' field"
            print(f"❌ {error_msg}")
            return jsonify({
                "error": error_msg, 
                "msg": "Vous devez fournir une 'question'",
                "received_fields": list(data.keys())
            }), 422
        
        # Validation du type
        if not isinstance(question, str):
            error_msg = f"Question must be a string, got {type(question)}"
            print(f"❌ {error_msg}")
            return jsonify({
                "error": error_msg,
                "msg": "La question doit être une chaîne de caractères"
            }), 422
        
        # Nettoyage et validation de la longueur
        question = question.strip()
        print(f"🔍 Question nettoyée: '{question}' (longueur: {len(question)})")
        
        if not question:
            error_msg = "Question cannot be empty"
            print(f"❌ {error_msg}")
            return jsonify({
                "error": error_msg,
                "msg": "La question ne peut pas être vide"
            }), 422
        
        if len(question) < 3:
            error_msg = f"Question too short: {len(question)} characters"
            print(f"❌ {error_msg}")
            return jsonify({
                "error": error_msg,
                "msg": "La question doit contenir au moins 3 caractères"
            }), 422

        # Vérifier la disponibilité de l'assistant
        if not assistant:
            error_msg = "Assistant not available"
            print(f"❌ {error_msg}")
            return jsonify({
                "error": error_msg,
                "msg": "Service temporairement indisponible"
            }), 503

        print(f"🚀 Traitement de la question: '{question}'")
        
        # Traitement de la question
        try:
            sql_query, response = assistant.ask_question(question)
            print(f"✅ Réponse générée avec succès")
            print(f"SQL: {sql_query}")
            print(f"Réponse: {response}")
            
            return jsonify({
                "sql_query": sql_query,
                "response": response,
                "status": "success"
            }), 200
            
        except Exception as e:
            error_msg = f"Erreur dans le traitement: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            current_app.logger.error(error_msg)
            return jsonify({
                "error": "Processing error",
                "msg": f"Erreur lors du traitement de votre question: {str(e)}"
            }), 500
        
    except Exception as e:
        error_msg = f"Erreur générale: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        current_app.logger.error(error_msg)
        return jsonify({
            "error": "Server error",
            "msg": f"Erreur serveur: {str(e)}"
        }), 500

@agent_bp.route('/ask', methods=['GET'])
def ask_info():
    """Information sur l'endpoint ask"""
    return jsonify({
        "message": "Agent IA prêt à recevoir les questions 📚🧠",
        "endpoint": "/api/ask",
        "method": "POST",
        "required_fields": ["question"],
        "accepted_fields": ["question", "subject"],  # Nouveauté
        "assistant_status": "OK" if assistant else "ERROR",
        "example": {
            "question": "Combien d'élèves sont inscrits cette année?"
        }
    }), 200

@agent_bp.route('/debug', methods=['POST'])
def debug_request():
    """Endpoint de debug pour diagnostiquer les problèmes"""
    print("=== DEBUG REQUEST ===")
    current_app.logger.info("=== DEBUG REQUEST ===")
    
    debug_info = {
        "headers": dict(request.headers),
        "content_type": request.content_type,
        "is_json": request.is_json,
        "method": request.method,
        "url": request.url,
        "assistant_available": assistant is not None,
        "raw_data": None,
        "json_data": None,
        "error": None
    }
    
    # Données brutes
    try:
        debug_info["raw_data"] = request.data.decode('utf-8') if request.data else None
        print(f"Raw data: {debug_info['raw_data']}")
    except Exception as e:
        debug_info["error"] = f"Error reading raw data: {str(e)}"
    
    # Données JSON
    try:
        debug_info["json_data"] = request.get_json()
        print(f"JSON data: {debug_info['json_data']}")
    except Exception as e:
        debug_info["error"] = f"Error parsing JSON: {str(e)}"
    
    # Log complet
    for key, value in debug_info.items():
        print(f"{key}: {value}")
        current_app.logger.info(f"{key}: {value}")
    
    return jsonify(debug_info), 200

@agent_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "OK",
        "message": "Backend is running",
        "agent_status": "OK" if assistant else "ERROR",
        "assistant_available": assistant is not None
    }
    
    print(f"Health check: {health_status}")
    return jsonify(health_status), 200

@agent_bp.route('/test', methods=['GET'])
def test_agent():
    """Test simple de l'agent"""
    test_status = {
        "status": "Agent endpoint working",
        "assistant_available": assistant is not None,
        "timestamp": "2024-01-01 12:00:00"
    }
    
    print(f"Test agent: {test_status}")
    return jsonify(test_status), 200

# Error handlers pour ce blueprint
@agent_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "msg": "L'endpoint demandé n'existe pas"
    }), 404

@agent_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "error": "Method not allowed",
        "msg": "Méthode HTTP non autorisée pour cet endpoint"
    }), 405

@agent_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "msg": "Erreur interne du serveur"
    }), 500