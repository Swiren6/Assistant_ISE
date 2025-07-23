from flask import Blueprint, request, jsonify
from agent.assistant import SQLAssistant
from flask_jwt_extended import jwt_required  # facultatif si tu veux protéger l'accès
import logging

assistant = SQLAssistant()
agent_bp = Blueprint('agent_bp', __name__)
logger = logging.getLogger(__name__)

@agent_bp.route('/ask', methods=['POST'])
@jwt_required(optional=True)
def ask_sql():
    # Vérification du Content-Type
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        # Validation du champ 'question'
        if 'question' not in data or not isinstance(data['question'], str):
            return jsonify({"error": "Question must be a non-empty string"}), 422
            
        question = data['question'].strip()
        if not question:
            return jsonify({"error": "Question cannot be empty"}), 422

        # Logging pour débogage
        current_app.logger.info(f"Question reçue : {question}")
        
        try:
            sql_query, response = assistant.ask_question(question)
            return jsonify({
                "sql_query": sql_query,
                "response": response
            })
        except Exception as e:
            current_app.logger.error(f"Erreur de traitement : {str(e)}")
            return jsonify({"error": "Failed to process question"}), 500
            
    except Exception as e:
        current_app.logger.error(f"Erreur JSON : {str(e)}")
        return jsonify({"error": "Invalid request format"}), 400

@agent_bp.route('/ask', methods=['GET'])
def ask_info():
    return jsonify({"message": "Agent IA prêt à recevoir les questions 📚🧠"}), 200
