from colorama import init, Fore, Style
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
import shutil
from datetime import datetime
import sqlite3
import os


# Caminho do banco de dados
BASE_DIR = "C:\\ControleBiblioteca"
DB_PATH = os.path.join(BASE_DIR, "db", "emprestimos.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Larguras das colunas para listagens em console
W_TITULO = 35
W_ALUNO = 35
W_DATA = 12
W_DEV = 20
W_STATUS = 12

def inicializar_banco():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emprestimos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_emprestimo TEXT NOT NULL,
            data_devolucao TEXT,
            nome_aluno TEXT NOT NULL,
            serie TEXT NOT NULL,
            titulo_livro TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def imprimir_cabecalho(titulo="Empréstimos"):
    limpar_tela()
    print(Fore.GREEN + f"\n---------- {titulo} ----------" + Style.RESET_ALL)
    # Cabeçalho da tabela
    print(
        f"{'Título do Livro':{W_TITULO}} "
        f"{'Aluno (Série)':{W_ALUNO}} "
        f"{'Empréstimo':{W_DATA}}"
        f"{'Devolução':{W_DEV}}"
        f"{'Status':{W_STATUS}}"
    )
    print("-" * (W_TITULO + W_ALUNO + W_DATA + W_DEV + W_STATUS))

def formatar_linha(data_emp_str, data_dev_str, nome, serie, titulo):
    # se começa com "__/__/____", está emprestado; senão, devolvido
    status = "📕 Emprestado" if data_dev_str.startswith("__/__/____") else "✅ Devolvido"
    return (
        f"{titulo[:W_TITULO]:{W_TITULO}} "
        f"{(nome+' ('+serie+')')[:W_ALUNO]:{W_ALUNO}} "
        f"{data_emp_str:{W_DATA}}"
        f"{data_dev_str:{W_DEV}}"
        f"{status:{W_STATUS}}"
    )


def registrar_emprestimo():
    limpar_tela()
    print(Fore.GREEN + "\n---------- Novo Empréstimo ----------" + Style.RESET_ALL)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ==== BUSCAR ALUNO ====
    nome = ""
    serie = ""
    while True:
        termo = input("Digite parte do nome do aluno (ou Enter para digitar um novo): ").strip().upper()
        if termo == "":
            nome = input("Nome do aluno: ").strip().upper()
            serie = input("Série: ").strip().upper()
            break

        cursor.execute("""
            SELECT DISTINCT nome_aluno, serie FROM emprestimos
            WHERE nome_aluno LIKE ?
            ORDER BY nome_aluno
        """, (f"%{termo}%",))
        alunos = cursor.fetchall()

        if not alunos:
            print(Fore.YELLOW + "Nenhum aluno encontrado com esse termo." + Style.RESET_ALL)
            if input("Deseja digitar o nome manualmente? [s/n]: ").strip().lower() == 's':
                nome = input("Nome do aluno: ").strip().upper()
                serie = input("Série: ").strip().upper()
                break
            continue

        print("\nAlunos encontrados:")
        for i, (n, s) in enumerate(alunos, 1):
            print(f"{i:2}. {n} ({s})")

        escolha = input("\nDigite o número do aluno ou Enter para buscar novamente: ").strip()
        if escolha.isdigit() and 1 <= int(escolha) <= len(alunos):
            nome, serie = alunos[int(escolha)-1]
            break

    # ==== BUSCAR LIVRO ====
    titulo = ""
    while True:
        termo = input("\nDigite parte do título do livro (ou Enter para digitar um novo): ").strip().upper()
        if termo == "":
            titulo = input("Título do livro: ").strip().upper()
            break

        cursor.execute("""
            SELECT DISTINCT titulo_livro FROM emprestimos
            WHERE titulo_livro LIKE ?
            ORDER BY titulo_livro
        """, (f"%{termo}%",))
        livros = cursor.fetchall()

        if not livros:
            print(Fore.YELLOW + "Nenhum livro encontrado com esse termo." + Style.RESET_ALL)
            if input("Deseja digitar o título manualmente? [s/n]: ").strip().lower() == 's':
                titulo = input("Título do livro: ").strip().upper()
                break
            continue

        print("\nLivros encontrados:")
        for i, (t,) in enumerate(livros, 1):
            print(f"{i:2}. {t}")

        escolha = input("\nDigite o número do livro ou Enter para buscar novamente: ").strip()
        if escolha.isdigit() and 1 <= int(escolha) <= len(livros):
            titulo = livros[int(escolha)-1][0]
            break

    conn.close()

    data = datetime.now().strftime("%d/%m/%Y")
    print(f"\nConfirma registrar o seguinte empréstimo?")
    print("-" * 40)
    print(f"Aluno: {nome}\nSérie: {serie}\nLivro: {titulo}\nData : {data}")
    print("-" * 40)
    if input("[1] Confirmar | [2] Cancelar: ").strip() == '1':
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO emprestimos (data_emprestimo, nome_aluno, serie, titulo_livro)
            VALUES (?, ?, ?, ?);
        """, (data, nome, serie, titulo))
        conn.commit()
        conn.close()
        print(Fore.GREEN + "✅ Empréstimo registrado com sucesso!" + Style.RESET_ALL)
    else:
        print(Fore.MAGENTA + "❌ Operação cancelada." + Style.RESET_ALL)



def registrar_devolucao():
    limpar_tela()
    print(Fore.GREEN +"\n---------- Registrar Devolução ----------"+Style.RESET_ALL)
    termo = input("Digite nome do aluno ou título do livro: ").strip().upper()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, data_emprestimo, nome_aluno, serie, titulo_livro 
        FROM emprestimos 
        WHERE data_devolucao IS NULL AND 
              (nome_aluno LIKE ? OR titulo_livro LIKE ?)
    """, (f"%{termo}%", f"%{termo}%"))
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        print(Fore.MAGENTA+"❌ Nenhum empréstimo pendente encontrado."+Style.RESET_ALL)
        return

    # Impressão tabular
    print(Fore.GREEN +"\nEmpréstimos encontrados:"+Style.RESET_ALL)
    headers = ["#", "Nome do Aluno", "Título do Livro", "Série", "Data Empréstimo"]
    widths = [4, 30, 40, 8, 14]
    # cabeçalho
    header_line = (
        f"{headers[0]:<{widths[0]}}"
        f"{headers[1]:<{widths[1]}}"
        f"{headers[2]:<{widths[2]}}"
        f"{headers[3]:<{widths[3]}}"
        f"{headers[4]:<{widths[4]}}"
    )
    print(header_line)
    print("-" * sum(widths))
    # linhas
    for idx, (id_, data, nome, serie, titulo) in enumerate(resultados, start=1):
        line = (
            f"{idx:<{widths[0]}}"
            f"{nome[:widths[1]-1]:<{widths[1]}}"
            f"{titulo[:widths[2]-1]:<{widths[2]}}"
            f"{serie:<{widths[3]}}"
            f"{data:<{widths[4]}}"
        )
        print(line)

    escolha = input("\nNúmero da devolução ou Enter para cancelar: ").strip()
    if not escolha.isdigit() or not (1 <= int(escolha) <= len(resultados)):
        print(Fore.MAGENTA+"❌ Operação cancelada."+Style.RESET_ALL)
        return

    id_escolhido = resultados[int(escolha) - 1][0]
    data_dev = datetime.now().strftime("%d/%m/%Y")
    if input(f"Confirmar devolução em {data_dev}? [1] Sim | [2] Não: ").strip() != '1':
        print(Fore.MAGENTA+"❌ Operação cancelada."+Style.RESET_ALL)
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE emprestimos SET data_devolucao = ? WHERE id = ?",
        (data_dev, id_escolhido)
    )
    conn.commit()
    conn.close()
    print(Fore.GREEN+"✅ Devolução registrada com sucesso!"+Style.RESET_ALL)


def buscar_por_aluno():
    limpar_tela()
    nome = input(Fore.GREEN + "\n---------- Registrar Devolução ----------\nDigite nome (ou parte): " + Style.RESET_ALL).strip().upper()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT data_emprestimo, data_devolucao, nome_aluno, serie, titulo_livro 
        FROM emprestimos 
        WHERE nome_aluno LIKE ?
        ORDER BY
          substr(data_emprestimo, 7, 4)||'-'||substr(data_emprestimo, 4, 2)||'-'||substr(data_emprestimo, 1, 2)
    """, (f"%{nome}%",))
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        print(Fore.MAGENTA+"❌ Nenhum registro encontrado."+Style.RESET_ALL)
        return

    imprimir_cabecalho(f"Empréstimos de '{nome}'")
    for data_emp, data_dev, aluno, serie, titulo in resultados:
        dt_emp = datetime.strptime(data_emp, "%d/%m/%Y").strftime("%d/%m/%Y")
        if data_dev:
            dias = (datetime.strptime(data_dev, "%d/%m/%Y") - datetime.strptime(data_emp, "%d/%m/%Y")).days
            dt_dev = f"{data_dev} ({dias}d)"
        else:
            dias = (datetime.now() - datetime.strptime(data_emp, "%d/%m/%Y")).days
            dt_dev = f"__/__/____ ({dias}d)"

        print(formatar_linha(dt_emp, dt_dev, aluno, serie, titulo))

def buscar_por_livro():
    limpar_tela()
    livro = input(Fore.GREEN + "\n--- Buscar por livro ---\nDigite título (ou parte): " + Style.RESET_ALL).strip().upper()

    if len(livro) < 3:
        print("O nome deve ter no mínimo 3 caracteres.")
        limpar_tela()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT data_emprestimo, data_devolucao, nome_aluno, serie, titulo_livro 
        FROM emprestimos 
        WHERE titulo_livro LIKE ?
        ORDER BY
          substr(data_emprestimo, 7, 4)||'-'||substr(data_emprestimo, 4, 2)||'-'||substr(data_emprestimo, 1, 2)
    """, (f"%{livro}%",))
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        print(Fore.MAGENTA+"❌ Nenhum registro encontrado."+Style.RESET_ALL)
        return

    imprimir_cabecalho(f"Empréstimos do livro '{livro}'")
    for data_emp, data_dev, aluno, serie, titulo in resultados:
        dt_emp = datetime.strptime(data_emp, "%d/%m/%Y").strftime("%d/%m/%Y")
        if data_dev:
            dias = (datetime.strptime(data_dev, "%d/%m/%Y") - datetime.strptime(data_emp, "%d/%m/%Y")).days
            dt_dev = f"{data_dev} ({dias}d)"
        else:
            dias = (datetime.now() - datetime.strptime(data_emp, "%d/%m/%Y")).days
            dt_dev = f"__/__/____ ({dias}d)"

        print(formatar_linha(dt_emp, dt_dev, aluno, serie, titulo))

def listar_ativos():
    limpar_tela()
    imprimir_cabecalho("Empréstimos Ativos")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT data_emprestimo, NULL, nome_aluno, serie, titulo_livro
        FROM emprestimos
        WHERE data_devolucao IS NULL
        ORDER BY substr(data_emprestimo, 7, 4)||'-'||substr(data_emprestimo, 4, 2)||'-'||substr(data_emprestimo, 1, 2)
    """)
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        print(Fore.MAGENTA+"❌ Nenhum empréstimo ativo!"+Style.RESET_ALL)
        return


    for data_emp, _, aluno, serie, titulo in resultados:
        dias = (datetime.now() - datetime.strptime(data_emp, "%d/%m/%Y")).days
        dt_dev = f"__/__/____ ({dias}d)"
        print(formatar_linha(data_emp, dt_dev, aluno, serie, titulo))

# A função gerar_pdf_emprestimos_ativos permanece inalterada
def gerar_pdf_emprestimos_ativos():
    limpar_tela()
    print(Fore.GREEN+"\n📝 Gerando PDF dos Empréstimos Ativos..."+Style.RESET_ALL)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT data_emprestimo, nome_aluno, serie, titulo_livro 
        FROM emprestimos 
        WHERE data_devolucao IS NULL
        ORDER BY substr(data_emprestimo, 7, 4)||'-'||substr(data_emprestimo, 4, 2)||'-'||substr(data_emprestimo, 1, 2)
    """)
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        print(Fore.MAGENTA+"❌ Nenhum empréstimo ativo para gerar PDF!"+Style.RESET_ALL)
        return

    agora = datetime.now().strftime("%d-%m-%Y_%H-%M")
    nome_arquivo = os.path.join(BASE_DIR, f"emprestimos_ativos_{agora}.pdf")
    c = canvas.Canvas(nome_arquivo, pagesize=A4)
    c.setTitle("Empréstimos Ativos")
    largura, altura = A4

    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(largura / 2, altura - 2 * cm, "Empréstimos Ativos")
    c.setFont("Helvetica-Bold", 12)
    y = altura - 3 * cm

    # Cabeçalho com posições ajustadas
    cabeçalho = [
        ("Data", 1.5),
        ("Dias", 4.0),
        ("Aluno", 5.5),
        ("Série", 11),
        ("Livro", 13)
    ]
    for label, x_cm in cabeçalho:
        c.drawString(x_cm * cm, y, label)

    # Corpo
    y -= 0.5 * cm
    c.setFont("Helvetica", 10)
    for data_emp, nome, serie, titulo in resultados:
        if y < 2 * cm:
            c.showPage()
            y = altura - 2 * cm
            c.setFont("Helvetica", 9)

        dias = (datetime.now() - datetime.strptime(data_emp, "%d/%m/%Y")).days
        # Impressão nas novas posições
        c.drawString(1.5 * cm, y, data_emp)
        c.drawString(4.0 * cm, y, str(dias))
        c.drawString(5.5 * cm, y, nome[:24])
        c.drawString(11 * cm, y, serie)
        c.drawString(13* cm, y, titulo[:30])

        y -= 0.5 * cm

    c.save()
    print(f"📂 PDF gerado com sucesso: {nome_arquivo}")


def listar_todos():
    limpar_tela()
    imprimir_cabecalho("Todos os Empréstimos")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT data_emprestimo, data_devolucao, nome_aluno, serie, titulo_livro 
        FROM emprestimos 
        ORDER BY substr(data_emprestimo, 7, 4)||'-'||substr(data_emprestimo, 4, 2)||'-'||substr(data_emprestimo, 1, 2)
    """)
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        print("📂 Nenhum empréstimo encontrado.")
        return

    for data_emp, data_dev, aluno, serie, titulo in resultados:
        if data_dev:
            dias = (datetime.strptime(data_dev, "%d/%m/%Y") - datetime.strptime(data_emp, "%d/%m/%Y")).days
            dt_dev = f"{data_dev} ({dias}d)"
        else:
            dias = (datetime.now() - datetime.strptime(data_emp, "%d/%m/%Y")).days
            dt_dev = f"__/__/____ ({dias}d)"

        print(formatar_linha(data_emp, dt_dev, aluno, serie, titulo))

def limpar_tabela_emprestimos():
    limpar_tela()
    print(Fore.RED+"\n*** ATENÇÃO ***"+Style.RESET_ALL)
    print(Fore.GREEN+"Esta ação irá APAGAR TODOS os registros e REINICIAR o índice."+Style.RESET_ALL)
    if input("Digite 'SIM' para confirmar: ").strip().upper() == "SIM":
        agora = datetime.now()
        nome_bkp = f"emprestimos_bkp_{agora.strftime('%d_%m_%Y_%H_%M')}.db"
        caminho_bkp = os.path.join(os.path.dirname(DB_PATH), nome_bkp)
        shutil.copy2(DB_PATH, caminho_bkp)
        print(f"Backup criado: {caminho_bkp}")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM emprestimos")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='emprestimos'")
        conn.commit()
        conn.close()
        print("✅ Tabela limpa e índice reiniciado.")
    else:
        print(Fore.MAGENTA+"❌ Operação Cancelada."+Style.RESET_ALL)

from datetime import datetime
import sqlite3
import os

DB_PATH = os.path.join(BASE_DIR, "db", "emprestimos.db")

def estatisticas():
    limpar_tela()
    print(Fore.GREEN +"\n---------- Estatísticas ----------"+Style.RESET_ALL)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Quantidade de empréstimos ativos
    cursor.execute("""
        SELECT COUNT(id)
        FROM emprestimos
        WHERE data_devolucao IS NULL
    """)
    ativos = cursor.fetchone()[0]

    # Quantidade de empréstimos devolvidos
    cursor.execute("""
        SELECT COUNT(id)
        FROM emprestimos
        WHERE data_devolucao IS NOT NULL
    """)
    devolvidos = cursor.fetchone()[0]

    total = ativos + devolvidos

    # Busca todas as datas de empréstimo e devolução para calcular média
    cursor.execute("""
        SELECT data_emprestimo, data_devolucao
        FROM emprestimos
        WHERE data_devolucao IS NOT NULL
    """)
    rows = cursor.fetchall()

    conn.close()

    if total == 0:
        print("📂 Nenhum empréstimo encontrado.")
        return

    # Cálculo do tempo médio de empréstimo (apenas os devolvidos)
    dias_list = []
    for data_emp, data_dev in rows:
        d_emp = datetime.strptime(data_emp, "%d/%m/%Y")
        d_dev = datetime.strptime(data_dev, "%d/%m/%Y")
        dias_list.append((d_dev - d_emp).days)

    avg = sum(dias_list) / len(dias_list) if dias_list else 0

    # Exibição
    print(f"Total de empréstimos:         {total}")
    print(f"Empréstimos ativos:           {ativos}")
    print(f"Empréstimos devolvidos:       {devolvidos}")
    if dias_list:
        print(f"Tempo médio de empréstimo:    {avg:.2f} dias")
    else:
        print("Tempo médio de empréstimo:    N/A")
        

def listar_mais_antigos():
    """
    Pergunta ao usuário a quantidade de meses e
    lista os empréstimos ativos há pelo menos esse período,
    seguindo o padrão de apresentação de `listar_todos`.
    """
    limpar_tela()

    # recebe e valida input
    try:
        meses = int(input("Informe a quantidade mínima de meses: ").strip())
        if meses < 0:
            raise ValueError
    except ValueError:
        print(Fore.MAGENTA+"⛔ Valor inválido. Digite um número inteiro de meses."+Style.RESET_ALL)
        return

    imprimir_cabecalho(f"Empréstimos com mais de {meses} meses")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT data_emprestimo, nome_aluno, serie, titulo_livro
        FROM emprestimos
        WHERE data_devolucao IS NULL
        ORDER BY
        serie,
        date(
            substr(data_emprestimo,7,4) || '-' ||
            substr(data_emprestimo,4,2) || '-' ||
            substr(data_emprestimo,1,2)
        )        
    """)
    resultados = cursor.fetchall()
    conn.close()

    hoje = datetime.now()
    filtrados = []
    for data_str, nome, serie, titulo in resultados:
        try:
            d_emp = datetime.strptime(data_str, "%d/%m/%Y")
        except ValueError:
            continue
        diff_meses = (hoje.year - d_emp.year) * 12 + (hoje.month - d_emp.month)
        if diff_meses >= meses:
            filtrados.append((data_str, nome, serie, titulo, diff_meses))

    if not filtrados:
        print("🎉 "+ Fore.MAGENTA + "Não há empréstimos tão antigos.")
        return

    # Define série_antiga antes do loop
    serie_antiga = None

    for data_str, nome, serie, titulo, diff_meses in filtrados:
        # Se já tivermos uma série anterior e ela for diferente da atual, imprime a linha tracejada
        if serie_antiga is not None and serie != serie_antiga:
            total_width = W_TITULO + W_ALUNO + W_DATA + W_DEV + W_STATUS
            print("-" * total_width)

        # Formata data de devolução como meses
        dt_dev = f"__/__/____ ({diff_meses}m)"
        # Imprime a linha de dados
        print(formatar_linha(data_str, dt_dev, nome, serie, titulo))


        serie_antiga = serie



def menu():

    opções = [
        Fore.YELLOW +" Registrar novo empréstimo"+Style.RESET_ALL,
        Fore.YELLOW +" Registrar devolução"+Style.RESET_ALL,
        Fore.YELLOW +" Buscar por aluno"+Style.RESET_ALL,
        Fore.YELLOW +" Buscar por livro"+Style.RESET_ALL,
        Fore.YELLOW +" Listar empréstimos ativos"+Style.RESET_ALL,
        Fore.YELLOW +" Listar empréstimos ativos - PDF"+Style.RESET_ALL,
        Fore.YELLOW +" Listar todos os empréstimos"+Style.RESET_ALL,
        Fore.YELLOW +" Listar antigos por meses"+Style.RESET_ALL,
        Fore.YELLOW +" Estatísticas"+Style.RESET_ALL,
        # Fore.YELLOW +"Deletar dados CUIDADO"+Style.RESET_ALL,
        Fore.YELLOW+"Sair"+Style.RESET_ALL
    ]

    while True:
        print(Fore.CYAN +"\n========= CONTROLE DE BIBLIOTECA v. 1.0 ========="+Style.RESET_ALL)
        print(Fore.CYAN +"             Prof Vicente G M Junior           "+Style.RESET_ALL)
        print(Fore.GREEN +"Menu\n"+Style.RESET_ALL)

        for i, texto in enumerate(opções, start=1):
            print(f"{i}. {texto}")
        opcao = input("Escolha uma opção e Enter\n(ou somente Enter para limpar a tela): ").strip()



        # Se apertar só Entere
        if opcao == "":
            limpar_tela()
            continue

        # Se apertar numero maior que 10
        if opcao not in ["1", "2", "3","4", "5", "6", "7", "8", "9", "10"]:
            limpar_tela()
            continue

        {
            '1': registrar_emprestimo,
            '2': registrar_devolucao,
            '3': buscar_por_aluno,
            '4': buscar_por_livro,
            '5': listar_ativos,
            '6': gerar_pdf_emprestimos_ativos,
            '7': listar_todos,
            '8': listar_mais_antigos,
            '9': estatisticas,
            # '10': limpar_tabela_emprestimos,
            '10': exit
        }.get(opcao, lambda: print("Opção inválida!"))()




if __name__ == "__main__":
    inicializar_banco()
    menu()


