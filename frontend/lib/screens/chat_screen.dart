import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../widgets/custom_appbar.dart';
import '../widgets/message_bubble.dart';
import '../widgets/sidebar_menu.dart';
import '../models/message_model.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../utils/constants.dart';
import 'dart:convert';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final List<Message> _messages = [];
  final ScrollController _scrollController = ScrollController();
  final ApiService _apiService = ApiService();
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _addWelcomeMessage();
  }

  void _addWelcomeMessage() {
    setState(() {
      _messages.add(
        Message.assistant(
          text: AppConstants.defaultWelcomeMessage,
        ),
      );
    });
  }

//   Future<void> _sendMessage() async {
//   if (_messageController.text.trim().isEmpty || _isLoading) return;

//   final userMessage = _messageController.text.trim();
//   _messageController.clear();

//   setState(() {
//     _messages.add(Message.user(text: userMessage));
//     _messages.add(Message.typing());
//     _isLoading = true;
//   });

//   try {
//     final authService = Provider.of<AuthService>(context, listen: false);
//     final token = authService.token;
    
//     if (token == null) {
//       throw ApiException('Authentification requise', 401);
//     }

//     final response = await _apiService.askQuestion(userMessage, token);
    
//     setState(() {
//       _messages.removeLast();
//       _messages.add(
//         Message.assistant(
//           text: response['response'] ?? 'Aucune réponse reçue',
//           sqlQuery: response['sql_query'],
//           tokensUsed: response['tokens_used'],
//           cost: response['cost']?.toDouble(),
//         ),
//       );
//       _isLoading = false;
//     });
//   } on ApiException catch (e) {
//     setState(() {
//       _messages.removeLast();
//       _messages.add(Message.error(text: 'Erreur: ${e.message}'));
//       _isLoading = false;
//     });

//     if (e.statusCode == 401) {
//       ScaffoldMessenger.of(context).showSnackBar(
//         SnackBar(content: Text('Veuillez vous reconnecter'))
//       );
//     }
//   } catch (e) {
//     setState(() {
//       _messages.removeLast();
//       _messages.add(Message.error(text: 'Erreur inattendue'));
//       _isLoading = false;
//     });
//   }
//   _scrollToBottom();
// }
  Future<void> _sendMessage() async {
  if (_messageController.text.trim().isEmpty || _isLoading) return;

  final userMessage = _messageController.text.trim();
  _messageController.clear();

  setState(() {
    _messages.add(Message.user(text: userMessage));
    _messages.add(Message.typing());
    _isLoading = true;
  });

  try {
    final authService = Provider.of<AuthService>(context, listen: false);
    final token = authService.token ?? '';
    
    // Debug: Afficher la requête avant envoi
    print('Envoi de la requête avec body: ${jsonEncode({'question': userMessage})}');
    
    final response = await _apiService.askQuestion(userMessage, token);
    
    // Debug: Afficher la réponse
    print('Réponse reçue: $response');
    
    setState(() {
      _messages.removeLast();
      _messages.add(
        Message.assistant(
          text: response['response'] ?? 'Aucune réponse reçue',
          sqlQuery: response['sql_query'],
        ),
      );
      _isLoading = false;
    });
  } on ApiException catch (e) {
    // Gestion améliorée des erreurs
    String errorMsg = 'Erreur: ${e.message}';
    if (e.statusCode == 422) {
      errorMsg = 'Question mal formulée. Veuillez reformuler.';
    }
    
    setState(() {
      _messages.removeLast();
      _messages.add(Message.error(text: errorMsg));
      _isLoading = false;
    });

    if (e.statusCode == 401) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Session expirée. Veuillez vous reconnecter.'))
      );
    }
  } catch (e) {
    setState(() {
      _messages.removeLast();
      _messages.add(Message.error(text: 'Erreur inattendue. Veuillez réessayer.'));
      _isLoading = false;
    });
  }
  _scrollToBottom();
}
  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: AppConstants.animationDurationShort,
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _clearChat() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Effacer la conversation'),
          content: const Text('Êtes-vous sûr de vouloir effacer toute la conversation ?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Annuler'),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                setState(() {
                  _messages.clear();
                });
                _addWelcomeMessage();
              },
              child: const Text('Effacer'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: CustomAppBar(
        title: 'Assistant Scolaire',
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _clearChat,
            tooltip: 'Nouvelle conversation',
          ),
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () => _showInfoDialog(),
            tooltip: 'Informations',
          ),
        ],
      ),
      drawer: const SidebarMenu(),
      body: Column(
        children: [
          if (_isLoading) 
            const LinearProgressIndicator(
              backgroundColor: Colors.transparent,
              valueColor: AlwaysStoppedAnimation<Color>(AppConstants.primaryColor),
            ),
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    AppConstants.primaryColor.withOpacity(0.05),
                    Colors.transparent,
                  ],
                ),
              ),
              child: _messages.isEmpty 
                  ? _buildEmptyState()
                  : ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppConstants.paddingSmall, 
                        vertical: AppConstants.paddingMedium,
                      ),
                      itemCount: _messages.length,
                      itemBuilder: (context, index) {
                        final message = _messages[index];
                        return MessageBubble(
                          message: message,
                          isMe: message.isMe,
                        );
                      },
                    ),
            ),
          ),
          _buildMessageInput(),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.chat_bubble_outline,
            size: 64,
            color: Colors.grey.shade400,
          ),
          const SizedBox(height: AppConstants.paddingMedium),
          Text(
            'Commencez une conversation',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              color: Colors.grey.shade600,
            ),
          ),
          const SizedBox(height: AppConstants.paddingSmall),
          Text(
            'Posez une question sur le système scolaire',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Colors.grey.shade500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageInput() {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppConstants.paddingMedium, 
        vertical: AppConstants.paddingMedium,
      ),
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        border: Border(
          top: BorderSide(
            color: Colors.grey.shade300,
            width: 0.5,
          ),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 8,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _messageController,
                decoration: InputDecoration(
                  hintText: 'Posez votre question...',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(AppConstants.radiusRound),
                    borderSide: BorderSide.none,
                  ),
                  filled: true,
                  fillColor: Colors.grey.shade100,
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: AppConstants.paddingLarge,
                    vertical: AppConstants.paddingMedium,
                  ),
                  suffixIcon: _messageController.text.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear),
                          onPressed: () {
                            _messageController.clear();
                            setState(() {});
                          },
                        )
                      : null,
                ),
                textCapitalization: TextCapitalization.sentences,
                maxLines: null,
                minLines: 1,
                maxLength: AppConstants.maxMessageLength,
                onSubmitted: (_) => _sendMessage(),
                onChanged: (_) => setState(() {}),
                enabled: !_isLoading,
              ),
            ),
            const SizedBox(width: AppConstants.paddingSmall),
            Container(
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: _isLoading
                      ? [Colors.grey.shade400, Colors.grey.shade500]
                      : [AppConstants.primaryColor, AppConstants.primaryColorDark],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
              ),
              child: IconButton(
                icon: _isLoading
                    ? SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      )
                    : const Icon(Icons.send, color: Colors.white),
                onPressed: _isLoading ? null : _sendMessage,
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showInfoDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Assistant Scolaire'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Cet assistant peut répondre à vos questions sur le système scolaire.'),
              const SizedBox(height: AppConstants.paddingMedium),
              Consumer<AuthService>(
                builder: (context, authService, child) {
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Utilisateur: ${authService.user?.idpersonne ?? "Non connecté"}'),
                      if (authService.user?.roles.isNotEmpty ?? false)
                        Text('Rôles: ${authService.user!.roles.join(", ")}'),
                    ],
                  );
                },
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Fermer'),
            ),
          ],
        );
      },
    );
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}