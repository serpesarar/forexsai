"""
Email Service using Resend
Handles verification emails and password reset
"""
import httpx
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

RESEND_API_KEY = settings.resend_api_key if hasattr(settings, 'resend_api_key') else None
FROM_EMAIL = "ForexsAI <noreply@forexsai.com>"
SITE_URL = "https://www.forexsai.com"

# Email template with ForexsAI branding
# Logo URL - upload your logo to a public URL (e.g., your domain or CDN)
LOGO_URL = "https://www.forexsai.com/logo.png"

def get_email_template(title: str, content: str, button_text: str, button_url: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0B1220;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0B1220; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #0d1829 0%, #131f33 100%); border-radius: 16px; overflow: hidden; box-shadow: 0 20px 60px rgba(0, 224, 198, 0.08);">
                    <!-- Header with Centered Round Logo -->
                    <tr>
                        <td style="padding: 40px 40px 20px 40px; text-align: center;">
                            <!-- Logo Circle -->
                            <div style="display: inline-block; width: 72px; height: 72px; border-radius: 50%; background: linear-gradient(135deg, rgba(0, 224, 198, 0.15) 0%, rgba(59, 130, 246, 0.15) 100%); padding: 4px; box-shadow: 0 8px 32px rgba(0, 224, 198, 0.2);">
                                <img src="{LOGO_URL}" alt="ForexsAI" style="width: 64px; height: 64px; border-radius: 50%; display: block; object-fit: cover;" />
                            </div>
                            <!-- Brand Name -->
                            <p style="margin: 16px 0 0 0; font-size: 20px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;">
                                Forexs<span style="background: linear-gradient(90deg, #00E0C6, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">AI</span>
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 20px 40px 20px 40px;">
                            <h1 style="margin: 0 0 20px 0; font-size: 26px; font-weight: 700; color: #ffffff; text-align: center;">
                                {title}
                            </h1>
                            <p style="margin: 0 0 30px 0; font-size: 15px; line-height: 1.7; color: #94a3b8; text-align: center;">
                                {content}
                            </p>
                            
                            <!-- Button -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{button_url}" style="display: inline-block; padding: 14px 36px; background: linear-gradient(135deg, #00E0C6 0%, #3B82F6 100%); color: #0B1220; text-decoration: none; font-size: 15px; font-weight: 700; border-radius: 50px; box-shadow: 0 4px 20px rgba(0, 224, 198, 0.35);">
                                            {button_text}
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 40px 32px 40px; border-top: 1px solid rgba(255, 255, 255, 0.06);">
                            <p style="margin: 0; font-size: 12px; color: #64748b; text-align: center; line-height: 1.6;">
                                Bu email ForexsAI tarafından gönderilmiştir.<br>
                                Eğer bu işlemi siz yapmadıysanız, bu emaili görmezden gelebilirsiniz.
                            </p>
                            <p style="margin: 16px 0 0 0; font-size: 11px; color: #475569; text-align: center;">
                                © 2024 ForexsAI - AI-Powered Market Analysis
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


async def send_email(to: str, subject: str, html: str) -> bool:
    """Send email using Resend API"""
    logger.info(f"[EMAIL] Sending to {to}, subject: {subject}")
    logger.info(f"[EMAIL] RESEND_API_KEY status: {'SET' if RESEND_API_KEY else 'NOT SET'}")
    
    if not RESEND_API_KEY:
        logger.error("RESEND_API_KEY not configured")
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": FROM_EMAIL,
                    "to": [to],
                    "subject": subject,
                    "html": html
                }
            )
            
            if response.status_code == 200:
                logger.info(f"Email sent to {to}")
                return True
            else:
                logger.error(f"Failed to send email: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return False


async def send_verification_email(to: str, token: str, full_name: Optional[str] = None) -> bool:
    """Send email verification link"""
    name = full_name or "Kullanıcı"
    verification_url = f"{SITE_URL}/verify-email?token={token}"
    
    html = get_email_template(
        title="Email Adresinizi Doğrulayın",
        content=f"Merhaba {name}! ForexsAI'ya hoş geldiniz. Hesabınızı aktifleştirmek için aşağıdaki butona tıklayın. Link 24 saat geçerlidir.",
        button_text="Email Adresimi Doğrula",
        button_url=verification_url
    )
    
    return await send_email(to, "ForexsAI - Email Doğrulama", html)


async def send_password_reset_email(to: str, token: str, full_name: Optional[str] = None) -> bool:
    """Send password reset link"""
    name = full_name or "Kullanıcı"
    reset_url = f"{SITE_URL}/reset-password?token={token}"
    
    html = get_email_template(
        title="Şifrenizi Sıfırlayın",
        content=f"Merhaba {name}! Şifrenizi sıfırlamak için bir talep aldık. Aşağıdaki butona tıklayarak yeni şifrenizi belirleyebilirsiniz. Link 1 saat geçerlidir.",
        button_text="Şifremi Sıfırla",
        button_url=reset_url
    )
    
    return await send_email(to, "ForexsAI - Şifre Sıfırlama", html)


async def send_welcome_email(to: str, full_name: Optional[str] = None, referral_code: str = "") -> bool:
    """Send welcome email after registration"""
    name = full_name or "Kullanıcı"
    
    html = get_email_template(
        title="ForexsAI'ya Hoş Geldiniz! 🚀",
        content=f"Merhaba {name}! Artık yapay zeka destekli trading analizlerine erişebilirsiniz. Arkadaşlarınızı davet edin ve Pro üyelik kazanın! Referans kodunuz: <strong>{referral_code}</strong>",
        button_text="Panele Git",
        button_url=SITE_URL
    )
    
    return await send_email(to, "ForexsAI'ya Hoş Geldiniz! 🚀", html)
