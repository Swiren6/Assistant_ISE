# import os
# import logging
# from pathlib import Path
# from flask import Flask, request
# from flask_cors import CORS
# from flask_jwt_extended import (
#     JWTManager,
#     jwt_required,
#     get_jwt_identity,
#     create_access_token
# )
# from datetime import timedelta
# # IMPORTANT: Charger .env AVANT les autres imports
# from dotenv import load_dotenv

# # Charger le fichier .env depuis le répertoire courant
# env_path = Path('.') / '.env'
# if env_path.exists():
#     load_dotenv(env_path)
#     print(f"✅ Fichier .env chargé depuis: {env_path.absolute()}")
# else:
#     print(f"⚠️ Fichier .env non trouvé à: {env_path.absolute()}")
#     # Essayer dans le répertoire parent
#     parent_env = Path('..') / '.env'
#     if parent_env.exists():
#         load_dotenv(parent_env)
#         print(f"✅ Fichier .env chargé depuis: {parent_env.absolute()}")

# # Vérification des variables critiques
# required_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
# missing_vars = [var for var in required_vars if not os.getenv(var)]

# if missing_vars:
#     print(f"❌ Variables d'environnement manquantes: {missing_vars}")
#     print("Veuillez vérifier votre fichier .env")
#     exit(1)

# print(f"🔍 Configuration MySQL:")
# print(f"  Host: {os.getenv('MYSQL_HOST')}")
# print(f"  User: {os.getenv('MYSQL_USER')}")
# print(f"  Database: {os.getenv('MYSQL_DATABASE')}")
# print(f"  Port: {os.getenv('MYSQL_PORT', '3306')}")



# # Import des routes
# from routes.auth import auth_bp
# from routes.agent import agent_bp
# from config.database import init_db

# def create_app():
#     app = Flask(__name__)
    
#     # Configuration JWT FIRST
#     app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
#     app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
#     app.config['JWT_TOKEN_LOCATION'] = ['headers']
#     jwt = JWTManager(app)  # Doit être avant les blueprints

#     # Configuration CORS
#     CORS(app, resources={
#         r"/api/*": {
#             "origins": "*",
#             "methods": ["GET", "POST", "OPTIONS"],
#             "allow_headers": ["Content-Type", "Authorization"]
#         }
#     })

#     # Initialisation de la base de données
#     init_db(app)

#     # Enregistrement des blueprints
#     from routes.auth import auth_bp
#     from routes.chat import chat_bp
#     app.register_blueprint(auth_bp, url_prefix='/api')
#     app.register_blueprint(agent_bp, url_prefix='/api')

#     # Route de test
#     @app.route('/api/test')
  
#     @jwt_required(optional=True)
#     def test_route():
#         current_user = get_jwt_identity()
#         return {
#             "status": "ok",
#             "user": current_user,
#             "message": "Backend fonctionnel"
#         }
#     # Route health
#     @app.route('/api/health')
#     def health_check():
#         return {"status": "healthy"}, 200

#     return app

    
# def main():
#     """Point d'entrée principal"""
#     # Configuration des logs
#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s - %(levelname)s - %(message)s',
#         datefmt='%Y-%m-%d %H:%M:%S'
#     )
    
#     # Création de l'application
#     app = create_app()
#     if not app:
#         print("❌ Impossible de créer l'application")
#         exit(1)
    
#     print("\n" + "="*60)
#     print("🚀 Assistant Scolaire - Backend démarré")
#     print("="*60)
#     print(f"📍 URL: http://localhost:5001")
#     print(f"🏥 Health check: http://localhost:5001/api/health")
#     print(f"🔑 Login: http://localhost:5001/api/login")
#     print(f"💬 Chat: http://localhost:5001/api/ask")
#     print("="*60)
    
#     # Démarrage du serveur
#     try:
#         app.run(
#             host='0.0.0.0', 
#             port=5001, 
#             debug=True,
#             use_reloader=True
#         )
#     except KeyboardInterrupt:
#         print("\n👋 Arrêt du serveur")
#     except Exception as e:
#         print(f"❌ Erreur serveur: {e}")


# if __name__ == "__main__":
#     main()

   
   
import os
import logging
from pathlib import Path
from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    get_jwt_identity,
    create_access_token
)
from datetime import timedelta
from dotenv import load_dotenv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
# 🔐 Charger .env
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Fichier .env chargé depuis: {env_path.absolute()}")
else:
    print(f"⚠️ Fichier .env non trouvé à: {env_path.absolute()}")
    parent_env = Path('..') / '.env'
    if parent_env.exists():
        load_dotenv(parent_env)
        print(f"✅ Fichier .env chargé depuis: {parent_env.absolute()}")

# 🔎 Vérification variables
required_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print(f"❌ Variables d'environnement manquantes: {missing_vars}")
    exit(1)

print(f"🔍 Configuration MySQL:")
print(f"  Host: {os.getenv('MYSQL_HOST')}")
print(f"  User: {os.getenv('MYSQL_USER')}")
print(f"  Database: {os.getenv('MYSQL_DATABASE')}")
print(f"  Port: {os.getenv('MYSQL_PORT', '3306')}")

# 🔌 Routes et DB
from routes.auth import auth_bp
from routes.agent import agent_bp
from config.database import init_db

def create_app():
    app = Flask(__name__)

    # 🔐 JWT config
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    jwt = JWTManager(app)

    # 🌍 CORS config
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # 🛠 Initialisation base de données
    init_db(app)

    # 🧩 Enregistrement des Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(agent_bp, url_prefix='/api')

    # 🔎 Routes de test
    @app.route('/api/test')
    @jwt_required(optional=True)
    def test_route():
        current_user = get_jwt_identity()
        return {
            "status": "ok",
            "user": current_user,
            "message": "Backend fonctionnel"
        }

    @app.route('/api/health')
    def health_check():
        return {"status": "healthy"}, 200

    return app

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    app = create_app()
    if not app:
        print("❌ Impossible de créer l'application")
        exit(1)

    print("\n" + "="*60)
    print("🚀 Assistant Scolaire - Backend démarré")
    print("="*60)
    print(f"📍 URL: http://localhost:5001")
    print(f"🏥 Health check: http://localhost:5001/api/health")
    print(f"🔑 Login: http://localhost:5001/api/login")
    print(f"💬 Chat: http://localhost:5001/api/ask")
    print("="*60)

    try:
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=True,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n👋 Arrêt du serveur")
    except Exception as e:
        print(f"❌ Erreur serveur: {e}")

if __name__ == "__main__":
    main()
