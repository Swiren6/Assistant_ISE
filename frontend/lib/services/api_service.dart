// 

import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../utils/constants.dart';

class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, [this.statusCode]);

  @override
  String toString() => '$message${statusCode != null ? ' (Code: $statusCode)' : ''}';
}

class ApiService {
  static const String baseUrl = AppConstants.apiBaseUrl;

  Map<String, String> _getHeaders(String? token) {
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
    };
  }

  /// Connexion utilisateur
  Future<Map<String, dynamic>> login(String loginIdentifier, String password) async {
    print('🔐 Tentative de connexion pour: $loginIdentifier');
    
    try {
      final uri = Uri.parse('$baseUrl/login');
      final headers = _getHeaders(null);
      final body = jsonEncode({
        'login_identifier': loginIdentifier,
        'password': password,
      });

      print('📤 Envoi vers: $uri');
      print('📤 Headers: $headers');
      print('📤 Body: $body');

      final response = await http.post(
        uri,
        headers: headers,
        body: body,
      ).timeout(const Duration(seconds: 10));

      print('📥 Response status: ${response.statusCode}');
      print('📥 Response body: ${response.body}');

      return _handleResponse(response);
    } on SocketException catch (e) {
      print('❌ SocketException: $e');
      throw ApiException('Pas de connexion internet');
    } on HttpException catch (e) {
      print('❌ HttpException: $e');
      throw ApiException('Erreur de connexion au serveur');
    } on FormatException catch (e) {
      print('❌ FormatException: $e');
      throw ApiException('Réponse invalide du serveur');
    } catch (e) {
      print('❌ Exception générale: $e');
      throw ApiException('Erreur inattendue: $e');
    }
  }

  /// Envoi d'une question au chat
  Future<Map<String, dynamic>> askQuestion(String question, String token) async {
    print('💬 Envoi de question: $question');
    print('🔑 Token: ${token.isNotEmpty ? 'présent' : 'absent'}');
    
    try {
      final uri = Uri.parse('$baseUrl/ask');
      final headers = {
      'Content-Type': 'application/json', // ← Essentiel
      'Accept': 'application/json',
      if (token.isNotEmpty) 'Authorization': 'Bearer $token',
    };
      final body = jsonEncode({'question': question.trim()});

      print('📤 Envoi vers: $uri');
      print('📤 Headers: $headers');
      print('📤 Body: $body');

      final response = await http.post(
      uri,
      headers: headers,
      body: body,
    ).timeout(const Duration(seconds: 30));


      print('📥 Response status: ${response.statusCode}');
      print('📥 Response headers: ${response.headers}');
      print('📥 Response body: ${response.body}');

      // Gestion spéciale du statut 401
      if (response.statusCode == 401) {
        throw ApiException('Session expirée, veuillez vous reconnecter', 401);
      }

      return _handleResponse(response);
    } on SocketException catch (e) {
      print('❌ SocketException: $e');
      throw ApiException('Pas de connexion internet');
    } on HttpException catch (e) {
      print('❌ HttpException: $e');
      throw ApiException('Erreur de connexion au serveur');
    } on http.ClientException catch (e) {
      print('❌ ClientException: $e');
      throw ApiException('Erreur de client HTTP');
    } catch (e) {
      print('❌ Exception générale: $e');
      if (e is ApiException) rethrow;
      throw ApiException('Erreur lors de la requête: ${e.toString()}');
    }
  }

  /// Test de connectivité
  Future<Map<String, dynamic>> healthCheck() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/health'),
        headers: _getHeaders(null),
      ).timeout(const Duration(seconds: 5));

      return _handleResponse(response);
    } catch (e) {
      throw ApiException('Service indisponible');
    }
  }

  /// Test de l'endpoint ask
  Future<Map<String, dynamic>> testAskEndpoint() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/ask'),
        headers: _getHeaders(null),
      ).timeout(const Duration(seconds: 5));

      return _handleResponse(response);
    } catch (e) {
      throw ApiException('Endpoint ask indisponible');
    }
  }

  /// Traite les réponses HTTP
  Map<String, dynamic> _handleResponse(http.Response response) {
    final statusCode = response.statusCode;
    
    print('🔍 Traitement de la réponse - Status: $statusCode');
    
    try {
      final data = jsonDecode(response.body);
      print('🔍 Data décodée: $data');
      
      if (statusCode >= 200 && statusCode < 300) {
        return data;
      } else {
        final message = data['error'] ?? data['message'] ?? 'Erreur inconnue';
        throw ApiException(message, statusCode);
      }
    } on FormatException catch (e) {
      print('❌ Erreur de format JSON: $e');
      print('❌ Response body: ${response.body}');
      
      if (statusCode >= 200 && statusCode < 300) {
        return {'message': 'Success'};
      } else {
        throw ApiException('Réponse serveur invalide', statusCode);
      }
    }
  }

  /// Requête GET générique avec logs
  Future<Map<String, dynamic>> get(String endpoint, {String? token}) async {
    try {
      final uri = Uri.parse('$baseUrl$endpoint');
      final headers = _getHeaders(token);
      
      print('📤 GET: $uri');
      print('📤 Headers: $headers');
      
      final response = await http.get(uri, headers: headers)
          .timeout(const Duration(seconds: 10));
      
      print('📥 GET Response: ${response.statusCode}');
      return _handleResponse(response);
    } catch (e) {
      throw ApiException('Erreur lors de la requête GET: $e');
    }
  }

  /// Requête POST générique avec logs
  Future<Map<String, dynamic>> post(String endpoint, Map<String, dynamic> data, {String? token}) async {
    try {
      final uri = Uri.parse('$baseUrl$endpoint');
      final headers = _getHeaders(token);
      final body = jsonEncode(data);
      
      print('📤 POST: $uri');
      print('📤 Headers: $headers');
      print('📤 Body: $body');
      
      final response = await http.post(uri, headers: headers, body: body)
          .timeout(const Duration(seconds: 10));
      
      print('📥 POST Response: ${response.statusCode}');
      return _handleResponse(response);
    } catch (e) {
      throw ApiException('Erreur lors de la requête POST: $e');
    }
  }
}