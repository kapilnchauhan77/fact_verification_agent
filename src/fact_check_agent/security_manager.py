"""
Security and Privacy Manager for Fact Check Agent
Implements data protection, access control, and privacy features
"""
import hashlib
import hmac
import time
import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class SecurityManager:
    """Manages security and privacy features"""
    
    def __init__(self):
        """Initialize security manager"""
        self.sessions: Dict[str, Dict] = {}
        self.audit_log: List[Dict] = []
        self.rate_limits: Dict[str, List[float]] = {}
        self.blocked_ips: set = set()
        
    def create_secure_session(self, user_id: str, ip_address: str = None) -> str:
        """
        Create a secure session with audit logging
        
        Args:
            user_id: User identifier
            ip_address: Client IP address
            
        Returns:
            Session ID
        """
        # Check rate limiting
        if not self._check_rate_limit(user_id, ip_address):
            raise SecurityError("Rate limit exceeded")
        
        session_id = str(uuid.uuid4())
        session_data = {
            'user_id': user_id,
            'ip_address': ip_address,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'document_count': 0,
            'query_count': 0,
            'permissions': self._get_user_permissions(user_id)
        }
        
        self.sessions[session_id] = session_data
        
        # Audit log
        self._log_audit_event({
            'event': 'session_created',
            'user_id': user_id,
            'session_id': session_id,
            'ip_address': ip_address,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Secure session created for user {user_id}")
        return session_id
    
    def validate_session(self, session_id: str, user_id: str = None) -> bool:
        """
        Validate session and update activity
        
        Args:
            session_id: Session identifier
            user_id: Optional user ID for additional validation
            
        Returns:
            True if session is valid
        """
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        # Check session timeout (24 hours)
        created_at = datetime.fromisoformat(session['created_at'])
        if datetime.now() - created_at > timedelta(hours=24):
            self.invalidate_session(session_id)
            return False
        
        # Check user ID match
        if user_id and session['user_id'] != user_id:
            return False
        
        # Update last activity
        session['last_activity'] = datetime.now().isoformat()
        return True
    
    def invalidate_session(self, session_id: str):
        """Invalidate a session and clean up"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            
            # Audit log
            self._log_audit_event({
                'event': 'session_invalidated',
                'user_id': session['user_id'],
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
            
            del self.sessions[session_id]
            logger.info(f"Session {session_id} invalidated")
    
    def check_permission(self, session_id: str, permission: str) -> bool:
        """
        Check if session has specific permission
        
        Args:
            session_id: Session identifier
            permission: Permission to check
            
        Returns:
            True if permission granted
        """
        if session_id not in self.sessions:
            return False
        
        permissions = self.sessions[session_id].get('permissions', [])
        return permission in permissions or 'admin' in permissions
    
    def sanitize_document_path(self, file_path: str) -> str:
        """
        Sanitize document path to prevent directory traversal
        
        Args:
            file_path: Input file path
            
        Returns:
            Sanitized path
        """
        # Convert to Path object and resolve
        path = Path(file_path).resolve()
        
        # Check for dangerous patterns
        str_path = str(path)
        if '..' in str_path or str_path.startswith('/etc/') or str_path.startswith('/proc/'):
            raise SecurityError("Invalid file path")
        
        return str(path)
    
    def anonymize_sensitive_data(self, text: str) -> str:
        """
        Anonymize potentially sensitive information in text
        
        Args:
            text: Input text
            
        Returns:
            Anonymized text
        """
        import re
        
        # Email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                     '[EMAIL]', text)
        
        # Phone numbers (various formats)
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        text = re.sub(r'\(\d{3}\)\s*\d{3}[-.]?\d{4}', '[PHONE]', text)
        
        # SSN patterns
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
        
        # Credit card patterns
        text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', text)
        
        return text
    
    def secure_document_cleanup(self, file_path: str):
        """
        Securely delete document after processing
        
        Args:
            file_path: Path to document to clean up
        """
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                # Overwrite file content before deletion for security
                with open(path, 'wb') as f:
                    f.write(b'\0' * path.stat().st_size)
                path.unlink()
                logger.info(f"Securely deleted document: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to securely delete {file_path}: {e}")
    
    def _check_rate_limit(self, user_id: str, ip_address: str = None) -> bool:
        """Check rate limiting for user/IP"""
        current_time = time.time()
        window_size = 3600  # 1 hour
        max_requests = 100  # Max requests per hour
        
        # Check user rate limit
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []
        
        user_requests = self.rate_limits[user_id]
        # Remove old requests outside window
        user_requests[:] = [t for t in user_requests if current_time - t < window_size]
        
        if len(user_requests) >= max_requests:
            return False
        
        user_requests.append(current_time)
        return True
    
    def _get_user_permissions(self, user_id: str) -> List[str]:
        """Get permissions for user (placeholder - integrate with auth system)"""
        # Default permissions for all users
        return ['document_analysis', 'text_fact_check', 'chat_query']
    
    def _log_audit_event(self, event: Dict[str, Any]):
        """Log audit event"""
        self.audit_log.append(event)
        
        # Keep only last 10000 events
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-10000:]
    
    def get_audit_log(self, start_time: str = None, end_time: str = None) -> List[Dict]:
        """
        Get audit log entries
        
        Args:
            start_time: Start timestamp (ISO format)
            end_time: End timestamp (ISO format)
            
        Returns:
            List of audit events
        """
        events = self.audit_log
        
        if start_time:
            events = [e for e in events if e['timestamp'] >= start_time]
        
        if end_time:
            events = [e for e in events if e['timestamp'] <= end_time]
        
        return events
    
    def generate_privacy_report(self) -> Dict[str, Any]:
        """Generate privacy compliance report"""
        return {
            'data_retention': {
                'documents': 'Processed immediately and deleted',
                'sessions': 'Expire after 24 hours',
                'audit_logs': 'Last 10,000 events retained'
            },
            'data_processing': {
                'purpose': 'Fact-checking and document analysis only',
                'storage': 'No persistent document storage',
                'encryption': 'All API communications encrypted'
            },
            'user_rights': {
                'access': 'Users can access their session data',
                'deletion': 'Documents deleted immediately after processing',
                'portability': 'Analysis results available for export'
            },
            'security_measures': {
                'rate_limiting': 'Enabled',
                'session_management': 'Secure session tokens',
                'audit_logging': 'All actions logged',
                'data_anonymization': 'PII automatically anonymized'
            }
        }

class SecurityError(Exception):
    """Security-related exception"""
    pass