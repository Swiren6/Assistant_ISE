import 'dart:convert';
import 'dart:io';
import 'dart:async';
import 'package:http/http.dart' as http;
import '../utils/constants.dart';

class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, [this.statusCode]);

  @override
  String toString() =>
      '$message${statusCode != null ? ' (Code: $statusCode)' : ''}';
}

class ApiService {
  static const String baseUrl = AppConstants.apiBaseUrl;
  static const Duration defaultTimeout = Duration(seconds: 30);

  Map<String, String> _getHeaders(String? token) {
    return {
      'Content-Type': 'application/json; charset=utf-8',
      'Accept': 'application/json',
      if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
    };
  }

  /// Test de connectivité avec le backend
  Future<bool> testConnection() async {
    try {
      final response =
          await get('/health', timeout: const Duration(seconds: 5));
      return response['status'] == 'OK';
    } catch (e) {
      print('❌ Test de connexion échoué: $e');
      return false;
    }
  }

  /// Connexion utilisateur
  Future<Map<String, dynamic>> login(
      String loginIdentifier, String password) async {
    final endpoint = '/login';
    print('🔐 Tentative de connexion pour: $loginIdentifier');

    try {
      final response = await post(
        endpoint,
        {
          'login_identifier': loginIdentifier,
          'password': password,
        },
        timeout: const Duration(seconds: 15),
      );

      print('✅ Connexion réussie');
      return response;
    } on ApiException {
      rethrow;
    } catch (e) {
      print('❌ Erreur de connexion: $e');
      throw ApiException('Erreur lors de la connexion');
    }
  }

  /// Envoi d'une question au chat
  // Dans votre api_service.dart, modifiez la méthode askQuestion pour débugger

Future<Map<String, dynamic>> askQuestion(
    String question, String token) async {
  final endpoint = '/ask';
  print('💬 Envoi de question: $question');
  print('🔑 Token: ${token.isNotEmpty ? "présent" : "absent"}');

  try {
    final trimmedQuestion = question.trim();
    if (trimmedQuestion.isEmpty) {
      throw ApiException('Veuillez entrer une question', 422);
    }

    final uri = Uri.parse('$baseUrl$endpoint');
    
    // 🔍 DEBUG: Headers exactement comme Postman
    final headers = {
      'Content-Type': 'application/json',  // ← Simplifié (pas de charset)
      'Accept': 'application/json',
      if (token.isNotEmpty) 'Authorization': 'Bearer $token',
    };

    // 🔍 DEBUG: Body exactement comme Postman
    final bodyMap = {'question': trimmedQuestion};
    final body = jsonEncode(bodyMap);

    // 🔍 LOGS DE DEBUG DÉTAILLÉS
    print('🔍 === DEBUG FLUTTER → FLASK ===');
    print('📤 URI: $uri');
    print('📤 Headers: $headers');
    print('📤 Body Map: $bodyMap');
    print('📤 Body JSON: $body');
    print('📤 Body Length: ${body.length}');
    print('📤 Body Bytes: ${utf8.encode(body)}');
    
    // Test: encoder manuellement comme Postman
    final alternativeBody = '{"question":"$trimmedQuestion"}';
    print('📤 Alternative Body: $alternativeBody');

    final response = await http
        .post(
          uri,
          headers: headers,
          body: body,  // Essayez aussi: alternativeBody
        )
        .timeout(const Duration(seconds: 30));

    print('📥 Response status: ${response.statusCode}');
    print('📥 Response headers: ${response.headers}');
    print('📥 Response body: ${response.body}');

    return _handleResponse(response);
  } catch (e) {
    print('❌ Erreur détaillée: $e');
    print('❌ Type erreur: ${e.runtimeType}');
    if (e is ApiException) rethrow;
    throw ApiException('Erreur lors de l\'envoi de la question');
  }
}

// Méthode de test pour comparer avec Postman
Future<void> testExactPostmanRequest() async {
  try {
    final uri = Uri.parse('http://localhost:5001/api/ask');
    
    // 🔍 Reproduire EXACTEMENT la requête Postman
    final headers = {
      'Content-Type': 'application/json',
    };
    
    final body = '{"question":"élèves"}';  // String littérale comme Postman
    
    print('🔍 === TEST EXACT POSTMAN ===');
    print('📤 URI: $uri');
    print('📤 Headers: $headers');
    print('📤 Body: $body');
    
    final response = await http.post(
      uri,
      headers: headers,
      body: body,
    );
    
    print('📥 Status: ${response.statusCode}');
    print('📥 Body: ${response.body}');
    
    if (response.statusCode == 200) {
      print('✅ Test Postman reproduction réussi !');
    } else {
      print('❌ Même avec reproduction Postman: ${response.statusCode}');
    }
  } catch (e) {
    print('❌ Erreur test Postman: $e');
  }
}
  Map<String, dynamic> _handleResponse(http.Response response) {
    final statusCode = response.statusCode;
    print('🔍 Traitement réponse - Status: $statusCode');

    try {
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      print('🔍 Data décodée: $data');

      if (statusCode >= 200 && statusCode < 300) {
        // 🔥 CORRECTION: Retourner les données telles quelles pour le login
        // Si c'est une réponse de chat, on formate
        if (data.containsKey('response') && data.containsKey('sql_query')) {
          return {
            'response': data['response'] ?? data['msg'] ?? 'Réponse reçue',
            'sql_query': data['sql_query'],
            'status': 'success',
          };
        } else {
          // Pour les autres cas (comme login), retourner les données brutes
          return data;
        }
      } else {
        final message = data['error'] ??
            data['message'] ??
            data['msg'] ??
            'Erreur serveur (code $statusCode)';
        throw ApiException(message, statusCode);
      }
    } on FormatException catch (e) {
      print('❌ Erreur de format JSON: $e');
      throw ApiException('Format de réponse invalide du serveur', statusCode);
    }
  }

  /// Test de l'endpoint ask
  Future<Map<String, dynamic>> testAskEndpoint() async {
    try {
      return await get('/ask', timeout: const Duration(seconds: 5));
    } catch (e) {
      throw ApiException('Endpoint ask indisponible');
    }
  }

  /// Vérification de santé du serveur
  Future<Map<String, dynamic>> healthCheck() async {
    return get('/health', timeout: const Duration(seconds: 5));
  }

  /// Requête GET générique
  Future<Map<String, dynamic>> get(
    String endpoint, {
    String? token,
    Duration? timeout,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl$endpoint');
      final headers = _getHeaders(token);

      print('📤 GET: $uri');

      final response = await http
          .get(uri, headers: headers)
          .timeout(timeout ?? defaultTimeout);

      print('📥 Response: ${response.statusCode}');
      return _handleResponse(response);
    } on SocketException {
      throw ApiException('Pas de connexion internet. Vérifiez votre réseau.');
    } on http.ClientException {
      throw ApiException('Impossible de se connecter au serveur.');
    } on TimeoutException {
      throw ApiException('Temps d\'attente dépassé. Le serveur ne répond pas.');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Erreur lors de la requête: ${e.toString()}');
    }
  }

  /// Requête POST générique
  Future<Map<String, dynamic>> post(
    String endpoint,
    Map<String, dynamic> data, {
    String? token,
    Duration? timeout,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl$endpoint');
      final headers = _getHeaders(token);
      final body = jsonEncode(data);

      print('📤 POST: $uri');
      print('📤 Body: $body');

      final response = await http
          .post(uri, headers: headers, body: body)
          .timeout(timeout ?? defaultTimeout);

      print('📥 Response: ${response.statusCode}');
      return _handleResponse(response);
    } on SocketException {
      throw ApiException('Pas de connexion internet. Vérifiez votre réseau.');
    } on http.ClientException {
      throw ApiException('Impossible de se connecter au serveur.');
    } on TimeoutException {
      throw ApiException('Temps d\'attente dépassé. Le serveur ne répond pas.');
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Erreur lors de la requête: ${e.toString()}');
    }
  }

  /// Test de diagnostic pour débugger les requêtes
  Future<Map<String, dynamic>> debugRequest(String question) async {
    try {
      final uri = Uri.parse('$baseUrl/debug');
      final headers = _getHeaders(null);
      final body = jsonEncode({'question': question});

      print('🔍 DEBUG REQUEST');
      print('📤 URI: $uri');
      print('📤 Headers: $headers');
      print('📤 Body: $body');

      final response = await http
          .post(uri, headers: headers, body: body)
          .timeout(const Duration(seconds: 10));

      print('📥 Debug Response: ${response.statusCode}');
      print('📥 Debug Body: ${response.body}');

      return _handleResponse(response);
    } catch (e) {
      print('❌ Debug Error: $e');
      throw ApiException('Debug request failed: $e');
    }
  }
}
