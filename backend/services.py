import os
import base64
import requests
import json
from openai import OpenAI
from dotenv import load_dotenv
from fpdf import FPDF

load_dotenv(override=True)

# Motor do Groq (Llama 3.3)
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def analyze_sbar(s, b, a, r):
    try:
        prompt = f"""
        Você é um Preceptor Médico Universitário de Excelência.
        Sua missão é ensinar, corrigir e guiar um aluno/médico residente através da ferramenta SBAR.
        
        SBAR ENVIADO PELO ALUNO:
        S (Situação): {s}
        B (Histórico): {b}
        A (Avaliação): {a}
        R (Recomendação): {r}

        Responda EXATAMENTE neste formato JSON, sendo extremamente didático:
        {{
            "avaliacao_do_professor": "Um parágrafo acolhedor e direto explicando o que ele acertou e qual foi a falha principal no raciocínio clínico.",
            "correcoes_didaticas": "Liste em tópicos (usando o símbolo -) os erros específicos de cada letra (S, B, A, R) e explique o PORQUÊ didaticamente.",
            "padrao_ouro": "Reescreva o SBAR inteiro de forma perfeita, técnica e clara, servindo como o gabarito ideal."
        }}
        """
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": "Você é um preceptor médico sênior e atencioso. Retorne apenas JSON válido."},
                {"role": "user", "content": prompt}
            ]
        )
        
        dados = json.loads(response.choices[0].message.content)
        print(">>> AULA DO PRECEPTOR GERADA COM SUCESSO!")
        return dados

    except Exception as e:
        print(f"!!! ERRO NA IA: {e}")
        return {
            "avaliacao_do_professor": f"Falha na comunicação com o preceptor IA: {e}",
            "correcoes_didaticas": "- Verifique a estabilidade da conexão ou a chave API.",
            "padrao_ouro": "Por favor, contate a Diretoria de Ensino."
        }

def criar_pdf(s, b, a, r, data_ia):
    pdf = FPDF()
    pdf.add_page()
    
    # Paleta de Cores de Elite
    AZUL_ESCURO = (15, 23, 42)
    AZUL_CLARO = (240, 244, 248)
    VERDE_ESCURO = (21, 128, 61)
    VERDE_CLARO = (240, 253, 244)
    CINZA_TEXTO = (50, 50, 50)
    VERMELHO_CORRECAO = (185, 28, 28)

    # Função para limpar caracteres que quebram o PDF
    def limpa(t): 
        return str(t).replace('*', '').replace('"', "'").encode('latin-1', 'replace').decode('latin-1')

    # CABEÇALHO
    pdf.set_fill_color(*AZUL_ESCURO)
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 18)
    pdf.cell(0, 15, "RELATORIO DE PRECEPTORIA - SBAR", ln=True, align="C")
    pdf.set_font("helvetica", "I", 11)
    pdf.cell(0, 5, "Hospital Universitario Sao Francisco na Providencia de Deus", ln=True, align="C")
    pdf.ln(15)

    # 1. O QUE O ALUNO ENVIOU
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(*AZUL_ESCURO)
    pdf.cell(0, 8, "1. SEU REGISTRO ORIGINAL:", ln=True)
    
    pdf.set_fill_color(*AZUL_CLARO)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(*CINZA_TEXTO)
    texto_aluno = f"S (Situacao): {s}\nB (Historico): {b}\nA (Avaliacao): {a}\nR (Recomendacao): {r}"
    pdf.multi_cell(0, 6, limpa(texto_aluno), fill=True)
    pdf.ln(8)

    # 2. AVALIAÇÃO DO PROFESSOR
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(*AZUL_ESCURO)
    pdf.cell(0, 8, "2. AVALIACAO DO PRECEPTOR:", ln=True)
    pdf.set_draw_color(*AZUL_ESCURO)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(*CINZA_TEXTO)
    pdf.multi_cell(0, 6, limpa(data_ia.get('avaliacao_do_professor', '')))
    pdf.ln(8)

    # 3. CORREÇÕES DIDÁTICAS
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(*VERMELHO_CORRECAO)
    pdf.cell(0, 8, "3. PONTOS DE ATENCAO E CORRECOES:", ln=True)
    pdf.set_draw_color(*VERMELHO_CORRECAO)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(*CINZA_TEXTO)
    pdf.multi_cell(0, 6, limpa(data_ia.get('correcoes_didaticas', '')))
    pdf.ln(10)

    # 4. GABARITO (PADRÃO OURO)
    pdf.set_fill_color(*VERDE_CLARO)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(*VERDE_ESCURO)
    pdf.cell(0, 10, " 4. GABARITO PADRAO-OURO (SBAR IDEAL)", ln=True, fill=True)
    
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(*CINZA_TEXTO)
    pdf.multi_cell(0, 6, limpa(data_ia.get('padrao_ouro', '')), fill=True)

    caminho = "avaliacao_sbar_oficial.pdf"
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
            "sender": {"name": "Preceptoria HUSF", "email": os.getenv("SMTP_USER", "contato@husf.com.br")},
            "to": [{"email": to_email}],
            "subject": "Sua Avaliação SBAR Chegou! - HUSF",
            "textContent": "Olá, Doutor(a)! O Preceptor IA já analisou o seu caso clínico. Segue em anexo o relatório detalhado em PDF com as correções e o gabarito padrão-ouro. Bons estudos!",
            "attachment": [{"content": pdf_base64, "name": "Relatorio_SBAR_HUSF.pdf"}]
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [201, 202]:
            print(">>> SUCESSO: E-mail de Elite enviado!")
        else:
            print(f"!!! ERRO NA API: {response.text}")
            
    except Exception as e:
        print(f"!!! ERRO FATAL DE ENVIO: {str(e)}")