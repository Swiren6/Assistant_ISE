// // import 'dart:convert';
// // import 'dart:io';
// // import 'package:http/http.dart' as http;
// // import '../utils/constants.dart';

// // class ApiException implements Exception {
// //   final String message;
// //   final int? statusCode;

// //   ApiException(this.message, [this.statusCode]);

// //   @override
// //   String toString() => message;
// // }

// // class ApiService {
// //   static const String baseUrl = AppConstants.apiBaseUrl;
// //   String? _authToken;

// //   // Headers par défaut
// //   Map<String, String> get _headers {
// //     final headers = {
// //       'Content-Type': 'application/json',
// //       'Accept': 'application/json',
// //     };
    
// //     if (_authToken != null) {
// //       headers['Authorization'] = 'Bearer $_authToken';
// //     }
    
// //     return headers;
// //   }

// //   /// Définit le token d'authentification
// //   void setAuthToken(String token) {
// //     _authToken = token;
// //   }

// //   /// Supprime le token d'authentification
// //   void clearAuthToken() {
// //     _authToken = null;
// //   }

// //   /// Connexion utilisateur
// //   Future<Map<String, dynamic>> login(String loginIdentifier, String password) async {
// //     try {
// //       final response = await http.post(
// //         Uri.parse('$baseUrl/login'),
// //         headers: _headers,
// //         body: jsonEncode({
// //           'login_identifier': loginIdentifier,
// //           'password': password,
// //         }),
// //       ).timeout(const Duration(seconds: 10));

// //       return _handleResponse(response);
// //     } on SocketException {
// //       throw ApiException('Pas de connexion internet');
// //     } on HttpException {
// //       throw ApiException('Erreur de connexion au serveur');
// //     } on FormatException {
// //       throw ApiException('Réponse invalide du serveur');
// //     } catch (e) {
// //       throw ApiException('Erreur inattendue: $e');
// //     }
// //   }

// //   /// Envoi d'une question au chat
// //   Future<Map<String, dynamic>> askQuestion(String question) async {
// //     try {
// //       final response = await http.post(
// //         Uri.parse('$baseUrl/ask'),
// //         headers: _headers,
// //         body: jsonEncode({
// //           'question': question,
// //         }),
// //       ).timeout(const Duration(seconds: 30));

// //       return _handleResponse(response);
// //     } on SocketException {
// //       throw ApiException('Pas de connexion internet');
// //     } on HttpException {
// //       throw ApiException('Erreur de connexion au serveur');
// //     } on FormatException {
// //       throw ApiException('Réponse invalide du serveur');
// //     } catch (e) {
// //       throw ApiException('Erreur inattendue: $e');
// //     }
// //   }

// //   /// Vérification de la santé du service
// //   Future<Map<String, dynamic>> healthCheck() async {
// //     try {
// //       final response = await http.get(
// //         Uri.parse('$baseUrl/health'),
// //         headers: _headers,
// //       ).timeout(const Duration(seconds: 5));

// //       return _handleResponse(response);
// //     } catch (e) {
// //       throw ApiException('Service indisponible');
// //     }
// //   }

// //   /// Traite les réponses HTTP
// //   Map<String, dynamic> _handleResponse(http.Response response) {
// //     final statusCode = response.statusCode;
    
// //     try {
// //       final Map<String, dynamic> data = jsonDecode(response.body);
      
// //       if (statusCode >= 200 && statusCode < 300) {
// //         return data;
// //       } else {
// //         final message = data['error'] ?? data['message'] ?? 'Erreur inconnue';
// //         throw ApiException(message, statusCode);
// //       }
// //     } on FormatException {
// //       if (statusCode >= 200 && statusCode < 300) {
// //         return {'message': 'Success'};
// //       } else {
// //         throw ApiException('Erreur serveur', statusCode);
// //       }
// //     }
// //   }

// //   /// Requête GET générique
// //   Future<Map<String, dynamic>> get(String endpoint) async {
// //     try {
// //       final response = await http.get(
// //         Uri.parse('$baseUrl$endpoint'),
// //         headers: _headers,
// //       ).timeout(const Duration(seconds: 10));

// //       return _handleResponse(response);
// //     } catch (e) {
// //       throw ApiException('Erreur lors de la requête GET: $e');
// //     }
// //   }

// //   /// Requête POST générique
// //   Future<Map<String, dynamic>> post(String endpoint, Map<String, dynamic> data) async {
// //     try {
// //       final response = await http.post(
// //         Uri.parse('$baseUrl$endpoint'),
// //         headers: _headers,
// //         body: jsonEncode(data),
// //       ).timeout(const Duration(seconds: 10));

// //       return _handleResponse(response);
// //     } catch (e) {
// //       throw ApiException('Erreur lors de la requête POST: $e');
// //     }
// //   }
// // }



// import 'dart:convert';
// import 'dart:io';
// import 'package:http/http.dart' as http;
// import 'package:provider/provider.dart';
// import 'package:flutter/material.dart';
// import '../services/auth_service.dart';
// import '../utils/constants.dart';

// class ApiException implements Exception {
//   final String message;
//   final int? statusCode;

//   ApiException(this.message, [this.statusCode]);

//   @override
//   String toString() => '$message${statusCode != null ? ' (Code: $statusCode)' : ''}';
// }

// class ApiService {
//   static const String baseUrl = AppConstants.apiBaseUrl;

//   Map<String, String> _getHeaders(String? token) {
//     final headers = {
//       'Content-Type': 'application/json',
//       'Accept': 'application/json',
//     };
    
//     if (token != null) {
//       headers['Authorization'] = 'Bearer $token';
//     }
    
//     return headers;
//   }

//   Future<Map<String, dynamic>> login(String loginIdentifier, String password) async {
//     try {
//       final response = await http.post(
//         Uri.parse('$baseUrl/login'),
//         headers: _getHeaders(null),
//         body: jsonEncode({
//           'login_identifier': loginIdentifier,
//           'password': password,
//         }),
//       ).timeout(const Duration(seconds: 10));

//       return _handleResponse(response);
//     } on SocketException {
//       throw ApiException('Pas de connexion internet');
//     } on http.ClientException {
//       throw ApiException('Erreur de connexion au serveur');
//     } on FormatException {
//       throw ApiException('Réponse invalide du serveur');
//     } catch (e) {
//       throw ApiException('Erreur inattendue: $e');
//     }
//   }

//   Future<Map<String, dynamic>> askQuestion(String question, String token) async {
//     try {
//       final response = await http.post(
//         Uri.parse('$baseUrl/ask'),
//         headers: _getHeaders(token),
//         body: jsonEncode({'question': question}),
//       ).timeout(const Duration(seconds: 30));

//       final data = _handleResponse(response);
      
//       if (response.statusCode == 401) {
//         throw ApiException('Authentification requise', 401);
//       }
      
//       return data;
//     } on SocketException {
//       throw ApiException('Pas de connexion internet');
//     } catch (e) {
//       throw ApiException('Erreur lors de la requête: ${e.toString()}');
//     }
//   }

//   Map<String, dynamic> _handleResponse(http.Response response) {
//     final statusCode = response.statusCode;
    
//     try {
//       final data = jsonDecode(response.body);
      
//       if (statusCode >= 200 && statusCode < 300) {
//         return data;
//       } else {
//         final message = data['error'] ?? data['message'] ?? 'Erreur inconnue';
//         throw ApiException(message, statusCode);
//       }
//     } on FormatException {
//       if (statusCode >= 200 && statusCode < 300) {
//         return {'message': 'Success'};
//       } else {
//         throw ApiException('Erreur serveur', statusCode);
//       }
//     }
//   }
// }

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
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  Future<Map<String, dynamic>> login(String loginIdentifier, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/login'),
        headers: _getHeaders(null),
        body: jsonEncode({
          'login_identifier': loginIdentifier,
          'password': password,
        }),
      ).timeout(const Duration(seconds: 10));

      return _handleResponse(response);
    } on SocketException {
      throw ApiException('Pas de connexion internet');
    } on http.ClientException {
      throw ApiException('Erreur de connexion au serveur');
    } on FormatException {
      throw ApiException('Réponse invalide du serveur');
    } catch (e) {
      throw ApiException('Erreur inattendue: $e');
    }
  }

  Future<Map<String, dynamic>> askQuestion(String question, String token) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/ask'),
        headers: _getHeaders(token),
        body: jsonEncode({'question': question}),
      ).timeout(const Duration(seconds: 30));

      return _handleResponse(response);
    } on SocketException {
      throw ApiException('Pas de connexion internet');
    } catch (e) {
      throw ApiException('Erreur lors de la requête: ${e.toString()}');
    }
  }

  Map<String, dynamic> _handleResponse(http.Response response) {
    final statusCode = response.statusCode;
    
    try {
      final data = jsonDecode(response.body);
      
      if (statusCode >= 200 && statusCode < 300) {
        return data;
      } else {
        final message = data['error'] ?? data['message'] ?? 'Erreur inconnue';
        throw ApiException(message, statusCode);
      }
    } on FormatException {
      throw ApiException('Réponse serveur invalide', statusCode);
    }
  }
}