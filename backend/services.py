import os
import base64
import requests
import json
from openai import OpenAI
from dotenv import load_dotenv
from fpdf import FPDF

load_dotenv(override=True)

# -------------------------------------------------------------
# LIGAÇÃO DO MOTOR GROQ (Usando a biblioteca da OpenAI)
# -------------------------------------------------------------
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def analyze_sbar(s, b, a, r):
    try:
        prompt = f"""
        Analise o SBAR abaixo.
        S: {s} | B: {b} | A: {a} | R: {r}

        Responda EXATAMENTE neste formato JSON, usando estas exatas chaves em minúsculo:
        {{
            "analise_critica": "sua avaliacao aqui",
            "pontos_de_melhoria": "o que melhorar aqui",
            "versao_senior": "texto ideal aqui"
        }}
        """
        
        # Chamada para o modelo Llama 3 (Ultra rápido e gratuito)
        response = client.chat.completions.create(
           model="llama-3.3-70b-versatile",
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": "Você é um preceptor médico sênior. Retorne apenas JSON válido."},
                {"role": "user", "content": prompt}
            ]
        )
        
        dados = json.loads(response.choices[0].message.content)
        print(f">>> GROQ RESPONDEU COM SUCESSO: {dados}")
        return dados

    except Exception as e:
        print(f"!!! AVISO: GROQ FALHOU. MOTIVO: {e}")
        return {
            "analise_critica": f"ALERTA: Erro na IA ({e}).",
            "pontos_de_melhoria": "Verifique a chave GROQ_API_KEY no painel do Railway.",
            "versao_senior": "Por favor, contate a Diretoria de Ensino."
        }

def criar_pdf(s, b, a, r, data_ia):
    pdf = FPDF()
    pdf.add_page()
    
    AZUL = (15, 23, 42)
    VERDE = (21, 128, 61)

    pdf.set_fill_color(*AZUL)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 18)
    pdf.cell(0, 20, "AVALIACAO DE DESEMPENHO SBAR", ln=True, align="C")
    
    pdf.ln(25)
    pdf.set_text_color(*AZUL)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Parecer do Preceptor IA", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 11)
    
    def limpa(t): return str(t).replace('*', '').encode('latin-1', 'replace').decode('latin-1')

    pdf.multi_cell(0, 6, limpa(data_ia.get('analise_critica', '')))
    pdf.ln(5)
    
    pdf.set_text_color(*VERDE)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 7, "O que pode melhorar:", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(0, 6, limpa(data_ia.get('pontos_de_melhoria', '')))
    pdf.ln(10)

    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("helvetica", "B", 10)
    pdf.multi_cell(0, 6, "Exemplo Padrao Ouro:\n" + limpa(data_ia.get('versao_senior', '')), fill=True)

    caminho = "avaliacao_sbar.pdf"
    pdf.output(caminho)
    return caminho

def send_email(to_email, data_ia, s, b, a, r):
    try:
        arquivo_pdf = criar_pdf(s, b, a, r, data_ia)
        with open(arquivo_pdf, "rb") as f:
            pdf_base64 = base64.b64encode(f.read()).decode('utf-8')
            
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": os.getenv("BREVO_API_KEY"),
            "content-type": "application/json"
        }
        
        payload = {
            "sender": {"name": "Preceptor SBAR", "email": os.getenv("SMTP_USER", "contato@husf.com.br")},
            "to": [{"email": to_email}],
            "subject": "Seu Feedback SBAR - HUSF",
            "textContent": "Olá! Segue em anexo a sua avaliação clínica SBAR em PDF.",
            "attachment": [{"content": pdf_base64, "name": "Feedback_SBAR.pdf"}]
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [201, 202]:
            print(">>> SUCESSO: E-mail enviado pela API do Brevo!")
        else:
            print(f"!!! ERRO NA API: {response.text}")
            
    except Exception as e:
        print(f"!!! ERRO FATAL DE ENVIO: {str(e)}")