from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
]
THIRD_PARTY_APPS = [
    "django_htmx",
]
LOCAL_APPS = [
    "apps.core",
    "apps.contas",
    "apps.clinica",
    "apps.pacientes",
    "apps.agenda",
    "apps.agendamentos",
    "apps.atendimentos",
    "apps.financeiro",
    "apps.site_publico",
    "apps.painel",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.middleware.AuditoriaMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.clinica",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
    }
}

AUTH_USER_MODEL = "contas.Usuario"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Fortaleza"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Regras de agendamento (confirmar valores com a clínica)
AGENDAMENTO_ANTECEDENCIA_MIN_HORAS = 2   # RN04: antecedência mínima para o paciente agendar
AGENDAMENTO_LIMITE_DIAS = 60             # RN04: até quantos dias à frente pode agendar
CANCELAMENTO_PRAZO_HORAS = 12            # RN05: prazo para o paciente cancelar ou remarcar pelo site

# Dados da clínica exibidos no site (troque pelos dados reais)
CLINICA = {
    "nome": "Saúde Agora",
    "cidade": "[Monte Alegre do Piauí]",
    "endereco": "[Endereço completo]",
    "bairro": "[Bairro]",
    "telefone": "(89) 98136-5009",
    "whatsapp": "5589981365009",           # só números, com 55 + DDD
    "whatsapp_exibicao": "(89) 98136-5009",
    "instagram": "",                       # ex.: https://instagram.com/saudeagora
    "facebook": "",
    "horario_semana": "Seg a Sex, 7h às 18h",
    "horario_sabado": "Sáb, 7h às 12h",
    "responsavel_tecnico": "[Nome do médico]",
    "responsavel_registro": "CRM [número]",
    "mapa_url": "",                        # link do Google Maps
    "foto_fachada": "img/clinica.jpg",     # deixe "" para mostrar o espaço vazio
}

# Login
LOGIN_URL = "contas:entrar"
LOGIN_REDIRECT_URL = "site_publico:inicio"
LOGOUT_REDIRECT_URL = "site_publico:inicio"
DEFAULT_FROM_EMAIL = "Saúde Agora <nao-responda@saudeagora.com.br>"
