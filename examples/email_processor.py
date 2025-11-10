# examples/email_processor.py
class SecureEmailProcessor:
    """
    Secure email processing for AI applications
    """
    
    def process_incoming_email(self, email_message):
        # Extract content from email
        email_content = self._extract_email_content(email_message)
        
        # Security analysis
        security_result = self.proxy.process_input(email_content, 'email')
        
        if not security_result.is_safe:
            # Quarantine email
            self._quarantine_email(email_message, security_result)
            return {
                'status': 'quarantined',
                'reason': 'security_threat',
                'threats': security_result.detected_threats
            }
        
        # Process safe email with AI
        ai_response = self.ai_service.process_email(
            security_result.sanitized_content
        )
        
        return {
            'status': 'processed',
            'ai_response': ai_response,
            'security_confidence': security_result.confidence_score
        }