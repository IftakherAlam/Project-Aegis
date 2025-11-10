# examples/crm_integration.py
class SecureCRMIntegration:
    """
    Example integration with Salesforce/CRM systems
    """
    
    def __init__(self, aegis_proxy):
        self.proxy = aegis_proxy
        self.crm_client = Salesforce(...)  # Your CRM client
    
    def get_customer_notes_safely(self, customer_id):
        # Fetch raw notes from CRM
        raw_notes = self.crm_client.get_notes(customer_id)
        
        # Process through Aegis security layer
        secure_notes = []
        for note in raw_notes:
            result = self.proxy.process_input(note['content'], 'crm_notes')
            
            if result.is_safe:
                secure_notes.append({
                    'id': note['id'],
                    'content': result.sanitized_content,
                    'original_timestamp': note['timestamp'],
                    'security_processed': datetime.now()
                })
            else:
                # Log security event
                self._log_security_incident(note, result.detected_threats)
                secure_notes.append({
                    'id': note['id'],
                    'content': '[SECURITY - CONTENT REMOVED]',
                    'original_timestamp': note['timestamp'],
                    'security_alert': 'Malicious content detected'
                })
        
        return secure_notes
    
    def _log_security_incident(self, original_note, threats):
        print(f"SECURITY ALERT - CRM Note {original_note['id']}")
        print(f"Threats: {threats}")
        # Integrate with your SIEM system here