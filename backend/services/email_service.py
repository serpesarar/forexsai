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
SITE_URL = "https://forexsai.com"

# Email template with ForexsAI branding
def get_email_template(title: str, content: str, button_text: str, button_url: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0a0f1a;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0f1a; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #0d1829 0%, #1a2744 100%); border-radius: 16px; overflow: hidden; box-shadow: 0 20px 60px rgba(0, 255, 200, 0.1);">
                    <!-- Header with Logo -->
                    <tr>
                        <td style="padding: 0;">
                            <img src="https://i.imgur.com/YourImageId.png" alt="ForexsAI" style="width: 100%; height: auto; display: block;" />
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 40px 20px 40px;">
                            <h1 style="margin: 0 0 20px 0; font-size: 28px; font-weight: 700; color: #ffffff; text-align: center;">
                                {title}
                            </h1>
                            <p style="margin: 0 0 30px 0; font-size: 16px; line-height: 1.6; color: #a0aec0; text-align: center;">
                                {content}
                            </p>
                            
                            <!-- Button -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{button_url}" style="display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, #00ffc8 0%, #00d9a8 100%); color: #0a0f1a; text-decoration: none; font-size: 16px; font-weight: 700; border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 255, 200, 0.4);">
                                            {button_text}
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px 40px 40px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                            <p style="margin: 0; font-size: 12px; color: #64748b; text-align: center;">
                                Bu email ForexsAI tarafından gönderilmiştir.<br>
                                Eğer bu işlemi siz yapmadıysanız, bu emaili görmezden gelebilirsiniz.
                            </p>
                            <p style="margin: 15px 0 0 0; font-size: 12px; color: #64748b; text-align: center;">
                                © 2024 ForexsAI - Yapay Zeka Destekli Trading
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
