import 'package:flutter/foundation.dart';
import '../models/user_model.dart';
import 'api_service.dart';
import 'storage_service.dart';

class AuthService with ChangeNotifier {
  UserModel? _user;
  String? _token;
  bool _isAuthenticated = false;
  bool _isLoading = false;
  String? _errorMessage;

  // Getters
  UserModel? get user => _user;
  String? get token => _token; // Getter public pour le token
  bool get isAuthenticated => _isAuthenticated;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  final ApiService _apiService = ApiService();
  final StorageService _storageService = StorageService();

  AuthService() {
    checkAuthStatus();
  }

  Future<void> checkAuthStatus() async {
    _setLoading(true);
    try {
      final token = await _storageService.getToken();
      final userData = await _storageService.getUserData();

      if (token != null && userData != null) {
        _token = token;
        _user = UserModel.fromJson(userData);
        _isAuthenticated = true;
      }
    } catch (e) {
      debugPrint('Erreur vérification statut auth: $e');
      await logout();
    } finally {
      _setLoading(false);
    }
  }

  Future<bool> login(String loginIdentifier, String password) async {
    _setLoading(true);
    _clearError();

    try {
      final response = await _apiService.login(loginIdentifier, password);
      
      if (response['token'] != null) {
        _token = response['token'];
        _user = UserModel.fromJson(response);
        _isAuthenticated = true;
        
        await _storageService.saveToken(_token!);
        await _storageService.saveUserData(response);
        return true;
      }
    } catch (e) {
      _setError(e.toString());
    } finally {
      _setLoading(false);
    }
    return false;
  }

  Future<void> logout() async {
    _setLoading(true);
    try {
      await _storageService.clearAll();
      _user = null;
      _token = null;
      _isAuthenticated = false;
      notifyListeners();
    } catch (e) {
      debugPrint('Erreur lors de la déconnexion: $e');
    } finally {
      _setLoading(false);
    }
  }

  Future<void> updateUser(UserModel updatedUser) async {
    _user = updatedUser;
    await _storageService.saveUserData(updatedUser.toJson());
    notifyListeners();
  }

  bool hasRole(String role) => _user?.hasRole(role) ?? false;
  bool get mustChangePassword => _user?.changepassword ?? false;

  // Méthodes privées
  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void _setError(String error) {
    _errorMessage = error;
    notifyListeners();
  }

  void _clearError() {
    _errorMessage = null;
    notifyListeners();
  }
}