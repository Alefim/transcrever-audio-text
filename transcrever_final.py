import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import speech_recognition as sr
from pydub import AudioSegment
import os
from fpdf import FPDF 
import threading 

# =====================================================================
# 🚨 CONFIGURAÇÕES E CONSTANTES (Mantenha seus caminhos CORRIGIDOS!) 🚨
# =====================================================================

# 1. CORREÇÃO DO FFmpeg (Se você usa arquivos que não são .wav)
# Mantenha o caminho EXATO do seu ffmpeg.exe:
try:
    # ⚠️ MUDE AQUI SE O SEU CAMINHO DO FFmpeg FOR DIFERENTE!
    AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe" 
except:
    pass

# Variáveis globais para a aplicação
ARQUIVO_WAV = "temp_audio_para_transcricao.wav"
r = sr.Recognizer()
caminho_audio_selecionado = "" 
NOME_ARQUIVO_PDF = "transcricao_final.pdf"

# =====================================================================
# Lógica de Transcrição e PDF
# =====================================================================

def salvar_como_pdf(texto, nome_arquivo_pdf, nome_original):
    """Função para criar um arquivo PDF com o texto."""
    
    pdf = FPDF()
    pdf.add_page()
    
    # Título
    pdf.set_font("Arial", "B", size=16)
    pdf.cell(200, 15, text="Transcrição de Áudio", new_x='LMARGIN', new_y='NEXT', align="C") 
    
    # Fonte do áudio
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, text=f"Fonte: {os.path.basename(nome_original)}", new_x='LEFT', new_y='NEXT', align="L")
    
    # Linha separadora
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 5, text="-"*60, new_x='LMARGIN', new_y='NEXT', align="C")
    
    # Corpo do texto
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 8, text=texto)
    
    # Salva o arquivo
    pdf.output(nome_arquivo_pdf)

def transcrever_audio(caminho_arquivo, status_label):
    """Executa a conversão, transcrição e salva o resultado em PDF (dentro de um Thread)."""
    
    if not caminho_arquivo:
        messagebox.showerror("Erro", "Nenhum arquivo de áudio foi selecionado.")
        # 🟢 CORREÇÃO 1/2: Configuração com 'fg' funciona no tk.Label
        status_label.config(text="Status: 🛑 Falhou (Nenhum arquivo)", fg="red")
        return

    # 🟢 CORREÇÃO 1/2: Configuração com 'fg' funciona no tk.Label
    status_label.config(text="Status: 🔄 Iniciando transcrição...", fg="blue")
    
    try:
        # --- ETAPA 1: Converter para WAV (se necessário) ---
        status_label.config(text="Status: ⚙️ Convertendo áudio para WAV...", fg="darkorange")
        audio = AudioSegment.from_file(caminho_arquivo)
        audio.export(ARQUIVO_WAV, format="wav")
        
        # --- ETAPA 2: Reconhecimento de Fala ---
        status_label.config(text="Status: 🎤 Aguardando API do Google (pode demorar)...", fg="purple")
        with sr.AudioFile(ARQUIVO_WAV) as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = r.record(source)
            
        texto = r.recognize_google(audio_data, language="pt-BR")
        
        # --- ETAPA 3: Salvamento e Finalização ---
        salvar_como_pdf(texto, NOME_ARQUIVO_PDF, caminho_arquivo)

        status_label.config(text=f"Status: ✅ Sucesso! PDF salvo como {NOME_ARQUIVO_PDF}", fg="green")
        
        # Mostra o texto transcrito em uma janela de mensagem
        messagebox.showinfo("Transcrição Concluída", f"O texto foi transcrito e salvo em {NOME_ARQUIVO_PDF}:\n\n{texto[:300]}...")
        
    except FileNotFoundError:
        msg = f"❌ ERRO CRÍTICO: Arquivo não encontrado! Verifique o caminho: {caminho_arquivo}"
        messagebox.showerror("Erro de Arquivo", msg)
        status_label.config(text="Status: 🛑 Falhou (Arquivo não encontrado)", fg="red")
        
    except Exception as e:
        msg = str(e)
        if "ffmpeg" in msg.lower() or "codec" in msg.lower():
            msg_final = "🚨 ERRO FFmpeg: O conversor de áudio não foi encontrado ou falhou. Verifique o caminho 'AudioSegment.converter'."
        elif "UnknownValueError" in msg:
            msg_final = "❌ ERRO: A API do Google não conseguiu entender a fala no áudio."
        elif "RequestError" in msg:
            msg_final = "❌ ERRO: Falha na conexão com a internet ou com a API do Google."
        else:
            msg_final = f"❌ ERRO INESPERADO: {msg}"
            
        messagebox.showerror("Erro de Transcrição", msg_final)
        status_label.config(text="Status: 🛑 Falhou", fg="red")
            
    finally:
        # Limpeza
        if os.path.exists(ARQUIVO_WAV):
            os.remove(ARQUIVO_WAV)

# =====================================================================
# Construção da Interface Tkinter
# =====================================================================

class AppTranscricao(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎤 Transcritor de Áudio Python")
        self.geometry("500x250")
        self.resizable(False, False)
        
        global caminho_audio_selecionado
        self.caminho_audio_selecionado = caminho_audio_selecionado
        
        # Configurar estilo (ttk é mais moderno, mas mantemos o Label antigo)
        style = ttk.Style(self)
        style.theme_use('clam')
        
        self.criar_widgets()

    def criar_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self, padding="20 20 20 20")
        main_frame.pack(fill='both', expand=True)
        
        # 1. Título
        ttk.Label(main_frame, text="Sistema de Transcrição de Áudio", font=('Helvetica', 14, 'bold')).pack(pady=10)

        # 2. Rótulo do Arquivo
        self.label_arquivo = ttk.Label(main_frame, text="Nenhum arquivo selecionado.", foreground="gray")
        self.label_arquivo.pack(pady=5)
        
        # 3. Botão de Seleção
        btn_selecionar = ttk.Button(main_frame, text="📂 Selecionar Arquivo de Áudio", command=self.selecionar_arquivo)
        btn_selecionar.pack(pady=10)
        
        # 4. Botão de Transcrição
        self.btn_transcrever = ttk.Button(main_frame, text="▶️ Iniciar Transcrição e Gerar PDF", command=self.iniciar_transcricao_thread, state=tk.DISABLED)
        self.btn_transcrever.pack(pady=10)
        
        # 5. Rótulo de Status
        # 🟢 CORREÇÃO 2/2: Trocamos ttk.Label para tk.Label para podermos usar a opção 'fg' (cor de frente)
        self.label_status = tk.Label(main_frame, text="Status: Aguardando arquivo...", font=('Helvetica', 10, 'italic'))
        self.label_status.pack(pady=10)

    def selecionar_arquivo(self):
        """Abre a caixa de diálogo para selecionar o arquivo."""
        caminho_selecionado = filedialog.askopenfilename(
            title="Selecione o Arquivo de Áudio",
            filetypes=[("Arquivos de Áudio", "*.mp3 *.wav *.ogg *.flac")]
        )
        
        if caminho_selecionado:
            self.caminho_audio_selecionado = caminho_selecionado
            nome_curto = os.path.basename(caminho_selecionado)
            self.label_arquivo.config(text=f"Arquivo: {nome_curto}", foreground="black")
            self.btn_transcrever.config(state=tk.NORMAL) # Ativa o botão de transcrever
            self.label_status.config(text="Status: Pronto para transcrever.", fg="blue")
        else:
            self.caminho_audio_selecionado = ""
            self.label_arquivo.config(text="Nenhum arquivo selecionado.", foreground="gray")
            self.btn_transcrever.config(state=tk.DISABLED) # Desativa o botão

    def iniciar_transcricao_thread(self):
        """Inicia a transcrição em uma thread separada para não travar a GUI."""
        # Desativa o botão enquanto processa
        self.btn_transcrever.config(state=tk.DISABLED)
        
        # Cria e inicia a thread
        thread_transcricao = threading.Thread(
            target=lambda: transcrever_audio(self.caminho_audio_selecionado, self.label_status)
        )
        thread_transcricao.start()
        
        self.after(100, self.checar_thread, thread_transcricao) # Começa a checar o status da thread

    def checar_thread(self, thread):
        """Verifica se a thread de transcrição terminou."""
        if thread.is_alive():
            # Se a thread ainda estiver rodando, checa novamente em 100ms
            self.after(100, self.checar_thread, thread)
        else:
            # Se a thread terminou, reativa o botão
            self.btn_transcrever.config(state=tk.NORMAL)

if __name__ == "__main__":
    app = AppTranscricao()
    app.mainloop()