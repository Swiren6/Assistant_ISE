# from flask import Blueprint, jsonify, request
# from flask_jwt_extended import jwt_required, get_jwt_identity
# from services.sql_assistant import SQLAssistant

# chat_bp = Blueprint('chat', __name__)

# # Instance globale de l'assistant SQL
# sql_assistant = SQLAssistant()

# @chat_bp.route('/ask', methods=['POST'])
# @jwt_required()
# def ask_question():
#     try:
#         current_user = get_jwt_identity()
#         data = request.get_json()
        
#         if not data or 'question' not in data:
#             return jsonify({"error": "Question manquante"}), 400
        
#         question = data['question']
        
#         # Traitement de la question via l'assistant SQL
#         sql_query, response, cost, tokens = sql_assistant.ask_question(question)
        
#         return jsonify({
#             "sql_query": sql_query,
#             "response": response,
#             "cost": cost,
#             "tokens_used": tokens,
#             "user_id": current_user['idpersonne']
#         })
        
#     except Exception as e:
#         return jsonify({"error": f"Erreur serveur: {str(e)}"}), 500

# @chat_bp.route('/health', methods=['GET'])
# def health_check():
#     return jsonify({"status": "ok", "service": "chat"})


from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.sql_assistant import SQLAssistant
import logging

chat_bp = Blueprint('chat', __name__)
logger = logging.getLogger(__name__)

# Instance globale de l'assistant SQL
sql_assistant = SQLAssistant()

@chat_bp.route('/ask', methods=['POST'])
@jwt_required()
def ask_question():
    try:
        # Debug: Log des headers et données reçues
        logger.info(f"Headers reçus: {request.headers}")
        logger.info(f"Données reçues: {request.get_json()}")
        
        current_user = get_jwt_identity()
        if not current_user:
            logger.error("Aucun utilisateur identifié dans le JWT")
            return jsonify({"error": "Authentification invalide"}), 401
        
        data = request.get_json()
        if not data or 'question' not in data:
            logger.error("Question manquante dans la requête")
            return jsonify({"error": "Le champ 'question' est requis"}), 400
        
        question = data['question']
        logger.info(f"Question reçue de {current_user['idpersonne']}: {question}")
        
        # Traitement de la question
        sql_query, response, cost, tokens = sql_assistant.ask_question(question)
        
        return jsonify({
            "sql_query": sql_query,
            "response": response,
            "cost": cost,
            "tokens_used": tokens,
            "user_id": current_user['idpersonne']
        })
        
    except Exception as e:
        logger.error(f"Erreur dans /api/ask: {str(e)}", exc_info=True)
        return jsonify({"error": "Erreur interne du serveur"}), 500

@chat_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "service": "chat",
        "mysql_connected": sql_assistant.mysql_connected
    })