import flet as ft
import pyodbc
import threading
import logging
from queue import Queue
from datetime import datetime
import pandas as pd
import csv
from reportlab.pdfgen import canvas

logging.basicConfig(level=logging.DEBUG)

def criar_conexao():
    try:
        connection = pyodbc.connect(
            r'DRIVER={SQL Server};'
            r'SERVER=26.192.40.39,1443;'  
            r'DATABASE=GEO_ITEQLESTE;'
            r'UID=Jorge1000;'
            r'PWD=N@talia161030;'
        )
        logging.debug("Conexão estabelecida com sucesso!")
        return connection
    except Exception as e:
        logging.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

def criar_pool_conexoes(tamanho_pool):
    pool = Queue(maxsize=tamanho_pool)
    for _ in range(tamanho_pool):
        conexao = criar_conexao()
        if conexao:
            pool.put(conexao)
    return pool

pool_conexoes = criar_pool_conexoes(20)

def search_database(query, params):
    conexao = pool_conexoes.get()
    if not conexao:
        return []
    try:
        cursor = conexao.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        return results
    except Exception as e:
        logging.error(f"Erro ao buscar dados: {e}")
        return []
    finally:
        pool_conexoes.put(conexao)

def insert_ocorrencia(matricula, nome, data, descricao, tipo, usuario):
    conexao = pool_conexoes.get()
    if not conexao:
        return False
    try:
        cursor = conexao.cursor()
        query = """INSERT INTO dbo.ocorrencias_novo (matricula_aluno, nome_aluno, data, descricao_novo, tipo, usuario)
                   VALUES (?, ?, CONVERT(DATETIME, ?, 120), ?, ?, ?)"""
        cursor.execute(query, (matricula, nome, data, descricao, tipo, usuario))
        conexao.commit()
        return True
    except Exception as e:
        logging.error(f"Erro ao inserir dados: {e}")
        return False
    finally:
        pool_conexoes.put(conexao)

def add_direitos_reservados():
    direitos_reservados = ft.Container(
        content=ft.Text("", color=ft.Colors.BLACK),
        alignment=ft.alignment.bottom_right,
        padding=ft.padding.all(10),
        margin=ft.margin.all(0),
        bgcolor=ft.Colors.TRANSPARENT
    )
    return direitos_reservados

def app_main(page: ft.Page, user):
    global matricula_field, nome_field, data_field

    page_size = 10
    columns_per_page = 7

    search_fields = {}
    suggestion_lists = {}
    data_tables = {}
    pagination_container = {}
    column_container = {}
    column_navigation_text = {}
    pagination_text = {}
    loading_indicators = {}
    tabs = {}
    current_page = {}
    current_col_start = {}

    queries = {
        "Pessoa": (
            "SELECT cod_pessoa, nome FROM dbo.pessoa WHERE nome LIKE ? OR cod_pessoa LIKE ?",
            "SELECT cod_pessoa, nome, Sexo, endereco_residencial, bairro_residencial, cidade_residencial, estado_residencial, cep_residencial, fone_residencial, celular, email, rg, cpf_cnpj, nascimento_data FROM dbo.pessoa WHERE cod_pessoa = ?",
            "SELECT cod_pessoa, nome, Sexo, endereco_residencial, bairro_residencial, cidade_residencial, estado_residencial, cep_residencial, fone_residencial, celular, email, rg, cpf_cnpj, nascimento_data FROM dbo.pessoa WHERE nome LIKE ?",
            ['Matricula', 'Nome', 'Sexo', 'Endereço', 'Bairro', 'Cidade', 'Estado', 'CEP', 'Telefone Residencial', 'Celular', 'Email', 'RG', 'CPF/CNPJ', 'Nascimento']
        ),
        "Documento": (
            "SELECT DISTINCT pd.cod_pessoa, p.nome AS nome_pessoa FROM dbo.PessoaDocumento pd INNER JOIN dbo.pessoa p ON pd.cod_pessoa = p.cod_pessoa WHERE p.nome LIKE ? OR pd.cod_pessoa LIKE ?",
            """SELECT pd.cod_pessoa, p.nome AS nome_pessoa, pd.cod_documento, 
                CASE 
                    WHEN pd.Cod_documento = '1' THEN '1_RG' 
                    WHEN pd.Cod_documento = '10' THEN '10_art_pub_1' 
                    WHEN pd.Cod_documento = '101' THEN '101_art_pub_2' 
                    WHEN pd.Cod_documento = '102' THEN '102_art_pub_3' 
                    WHEN pd.Cod_documento = '103' THEN '103_art_pub_4' 
                    WHEN pd.Cod_documento = '104' THEN '104_art_pub_5' 
                    WHEN pd.Cod_documento = '105' THEN '105_art_pub_6' 
                    WHEN pd.Cod_documento = '106' THEN '106_art_conc_pos2' 
                    WHEN pd.Cod_documento = '107' THEN '107_art_conc_pos3' 
                    WHEN pd.Cod_documento = '11' THEN '11_art_conc_pos' 
                    WHEN pd.Cod_documento = '12' THEN '12_art_conc_2licenc' 
                    WHEN pd.Cod_documento = '13' THEN '13_estagio' 
                    WHEN pd.Cod_documento = '2' THEN '2_CPF' 
                    WHEN pd.Cod_documento = '3' THEN '3_titulo_eleitor' 
                    WHEN pd.Cod_documento = '4' THEN '4_reservista' 
                    WHEN pd.Cod_documento = '5' THEN '5_cert_nascimento/casamento' 
                    WHEN pd.Cod_documento = '6' THEN '6_comprov_end' 
                    WHEN pd.Cod_documento = '7' THEN '7_hist_ens_med' 
                    WHEN pd.Cod_documento = '8' THEN '8_hist_1grad' 
                    WHEN pd.Cod_documento = '9' THEN '9_diploma_1grad' 
                END AS Cod_documentoN, 
                CASE WHEN pd.status = 'P' THEN 'Pendente' ELSE 'Entregue' END as status, 
                FORMAT(pd.data_entrega, 'dd/MM/yyyy') as data_entrega 
                FROM dbo.PessoaDocumento pd 
                INNER JOIN dbo.pessoa p ON pd.cod_pessoa = p.cod_pessoa 
                WHERE pd.cod_pessoa = ? 
                ORDER BY pd.data_entrega ASC""",
            """SELECT pd.cod_pessoa, p.nome AS nome_pessoa, pd.cod_documento, 
                CASE 
                    WHEN pd.Cod_documento = '1' THEN '1_RG' 
                    WHEN pd.Cod_documento = '10' THEN '10_art_pub_1' 
                    WHEN pd.Cod_documento = '101' THEN '101_art_pub_2' 
                    WHEN pd.Cod_documento = '102' THEN '102_art_pub_3' 
                    WHEN pd.Cod_documento = '103' THEN '103_art_pub_4' 
                    WHEN pd.Cod_documento = '104' THEN '104_art_pub_5' 
                    WHEN pd.Cod_documento = '105' THEN '105_art_pub_6' 
                    WHEN pd.Cod_documento = '106' THEN '106_art_conc_pos2' 
                    WHEN pd.Cod_documento = '107' THEN '107_art_conc_pos3' 
                    WHEN pd.Cod_documento = '11' THEN '11_art_conc_pos' 
                    WHEN pd.Cod_documento = '12' THEN '12_art_conc_2licenc' 
                    WHEN pd.Cod_documento = '13' THEN '13_estagio' 
                    WHEN pd.Cod_documento = '2' THEN '2_CPF' 
                    WHEN pd.Cod_documento = '3' THEN '3_titulo_eleitor' 
                    WHEN pd.Cod_documento = '4' THEN '4_reservista' 
                    WHEN pd.Cod_documento = '5' THEN '5_cert_nascimento/casamento' 
                    WHEN pd.Cod_documento = '6' THEN '6_comprov_end' 
                    WHEN pd.Cod_documento = '7' THEN '7_hist_ens_med' 
                    WHEN pd.Cod_documento = '8' THEN '8_hist_1grad' 
                    WHEN pd.Cod_documento = '9' THEN '9_diploma_1grad' 
                END AS Cod_documentoN, 
                CASE WHEN pd.status = 'P' THEN 'Pendente' ELSE 'Entregue' END as status, 
                FORMAT(pd.data_entrega, 'dd/MM/yyyy') as data_entrega 
                FROM dbo.PessoaDocumento pd 
                INNER JOIN dbo.pessoa p ON pd.cod_pessoa = p.cod_pessoa 
                WHERE p.nome LIKE ? 
                ORDER BY pd.data_entrega ASC""",
            ['Matricula', 'Nome', 'Código Documento', 'Nome Documento', 'Status', 'Data Entrega']
        ),
        "Certificado": (
            "SELECT DISTINCT pc.cod_pessoa, p.nome FROM dbo.Pessoa_Certificado pc INNER JOIN dbo.pessoa p ON pc.cod_pessoa = p.cod_pessoa WHERE p.nome LIKE ? OR pc.cod_pessoa LIKE ?",
            "SELECT pc.cod_pessoa, p.nome, pc.tipo_certificado, pc.cod_escola, pc.cod_curso, pc.cod_disciplina, d.nome AS nome_disciplina, pc.carga_horaria, pc.grade, pc.polo, FORMAT(pc.data_registro, 'dd/MM/yyyy') AS data_registro, pc.data_inicio, pc.data_conclusao, pc.data_emissao, pc.lote, pc.livro, pc.folha, pc.numero_registro, pc.cod_rastreamento, pc.retirado_por, pc.status, pc.observacao, pc.status_emissao, pc.data_solicitacao, pc.data_colacao_grau, pc.nota_tcc, pc.nota_01, pc.nota_02, pc.nota_03, pc.nota_04, pc.nota_05, pc.nota_06, pc.nota_07, pc.nota_08, pc.nota_09, pc.nota_10, pc.nota_11, pc.nota_12, pc.nota_13, pc.nota_14, pc.nota_15, pc.nota_16, pc.nota_17, pc.nota_18 FROM dbo.Pessoa_Certificado pc INNER JOIN dbo.pessoa p ON pc.cod_pessoa = p.cod_pessoa LEFT JOIN dbo.Disciplina d ON pc.cod_disciplina = d.cod_disciplina WHERE pc.cod_pessoa = ? ORDER BY pc.data_registro ASC",
            "SELECT pc.cod_pessoa, p.nome, pc.tipo_certificado, pc.cod_escola, pc.cod_curso, pc.cod_disciplina, d.nome AS nome_disciplina, pc.carga_horaria, pc.grade, pc.polo, FORMAT(pc.data_registro, 'dd/MM/yyyy') AS data_registro, pc.data_inicio, pc.data_conclusao, pc.data_emissao, pc.lote, pc.livro, pc.folha, pc.numero_registro, pc.cod_rastreamento, pc.retirado_por, pc.status, pc.observacao, pc.status_emissao, pc.data_solicitacao, pc.data_colacao_grau, pc.nota_tcc, pc.nota_01, pc.nota_02, pc.nota_03, pc.nota_04, pc.nota_05, pc.nota_06, pc.nota_07, pc.nota_08, pc.nota_09, pc.nota_10, pc.nota_11, pc.nota_12, pc.nota_13, pc.nota_14, pc.nota_15, pc.nota_16, pc.nota_17, pc.nota_18 FROM dbo.Pessoa_Certificado pc INNER JOIN dbo.pessoa p ON pc.cod_pessoa = p.cod_pessoa LEFT JOIN dbo.Disciplina d ON pc.cod_disciplina = d.cod_disciplina WHERE p.nome LIKE ? ORDER BY pc.data_registro ASC",
            ['Matricula', 'Nome', 'Tipo Certificado', 'Cod Escola', 'Cod Curso', 'Cod Disciplina', 'Nome Disciplina', 'Carga Horária', 'Grade', 'Polo', 'Data Registro', 'Data Início', 'Data Conclusão', 'Data Emissão', 'Lote', 'Livro', 'Folha', 'Número Registro', 'Cod Rastreamento', 'Retirado Por', 'Status', 'Observação', 'Status Emissao', 'Data Solicitação', 'Data Colacao Grau', 'Nota TCC', 'Nota 01', 'Nota 02', 'Nota 03', 'Nota 04', 'Nota 05', 'Nota 06', 'Nota 07', 'Nota 08', 'Nota 09', 'Nota 10', 'Nota 11', 'Nota 12', 'Nota 13', 'Nota 14', 'Nota 15', 'Nota 16', 'Nota 17', 'Nota 18']
        ),
        "Ocorrencia": (
            "SELECT DISTINCT o.matricula_aluno, p.nome FROM dbo.Ocorrencias o INNER JOIN dbo.pessoa p ON o.matricula_aluno = p.cod_pessoa WHERE p.nome LIKE ? OR o.matricula_aluno LIKE ?",
            "SELECT o.matricula_aluno, p.nome, o.tipo, FORMAT(o.data, 'dd/MM/yyyy') as data, o.hora, o.descricao, o.usuario, "
            "CASE WHEN po.tipo_observacao = 'F' THEN 'Financeiro' WHEN po.tipo_observacao = 'A' THEN 'Acadêmico' ELSE po.tipo_observacao END AS tipo_observacao, "
            "FORMAT(po.data_observacao, 'dd/MM/yyyy') as data_observacao, po.descricao AS descricao_observacao, po.hora AS hora_observacao "
            "FROM dbo.Ocorrencias o "
            "LEFT JOIN dbo.PessoaObservacao po ON o.matricula_aluno = po.cod_pessoa "
            "INNER JOIN dbo.pessoa p ON o.matricula_aluno = p.cod_pessoa "
            "WHERE o.matricula_aluno = ? "
            "ORDER BY o.data ASC",
            "SELECT o.matricula_aluno, p.nome, o.tipo, FORMAT(o.data, 'dd/MM/yyyy') as data, o.hora, o.descricao, o.usuario, "
            "CASE WHEN po.tipo_observacao = 'F' THEN 'Financeiro' WHEN po.tipo_observacao = 'A' THEN 'Acadêmico' ELSE po.tipo_observacao END AS tipo_observacao, "
            "FORMAT(po.data_observacao, 'dd/MM/yyyy') as data_observacao, po.descricao AS descricao_observacao, po.hora AS hora_observacao "
            "FROM dbo.Ocorrencias o "
            "LEFT JOIN dbo.PessoaObservacao po ON o.matricula_aluno = po.cod_pessoa "
            "INNER JOIN dbo.pessoa p ON o.matricula_aluno = p.cod_pessoa "
            "WHERE p.nome LIKE ? "
            "ORDER BY o.data ASC",
            ['Matricula', 'Nome', 'Tipo', 'Data', 'Hora', 'Descrição', 'Usuário', 'Tipo Observação', 'Data Observação', 'Descrição Observação', 'Hora Observação']
        ),
        "Nota/Falta": (
            "SELECT DISTINCT nf.matricula_aluno, p.nome FROM dbo.NotaFalta nf INNER JOIN dbo.pessoa p ON nf.matricula_aluno = p.cod_pessoa WHERE p.nome LIKE ? OR nf.matricula_aluno LIKE ?",
            """SELECT nf.matricula_aluno, p.nome, nf.media_final, 
                      d.nome AS nome_disciplina, nf.cod_turma, t.cod_curso, 
                      c.nome AS nome_curso,
                      nf.cod_disciplina, 
                      nf.situacao, 
                      nf.carga_horaria, 
                      CASE WHEN aae.cod_turma = nf.cod_turma THEN aae.descricao_atividade ELSE NULL END AS descricao_atividade_extra, 
                      CASE WHEN aae.cod_turma = nf.cod_turma THEN aae.data_atividade ELSE NULL END AS data_atividade_extra, 
                      CASE WHEN aae.cod_turma = nf.cod_turma THEN aae.carga_horaria ELSE NULL END AS carga_horaria_extra,
                      CASE WHEN aae.cod_turma = nf.cod_turma THEN aae.tipo_atividade ELSE NULL END AS tipo_atividade_extra
                FROM dbo.NotaFalta nf 
                JOIN dbo.Disciplina d ON nf.cod_disciplina = d.cod_disciplina 
                JOIN dbo.Turma t ON nf.cod_turma = t.cod_turma 
                JOIN dbo.Curso c ON t.cod_curso = c.cod_curso 
                INNER JOIN dbo.pessoa p ON nf.matricula_aluno = p.cod_pessoa 
                LEFT JOIN dbo.Aluno_AtividadesExtras aae ON nf.matricula_aluno = aae.matricula_aluno
                WHERE nf.matricula_aluno = ?
                ORDER BY c.nome""",
            """SELECT nf.matricula_aluno, p.nome, nf.media_final, 
                      d.nome AS nome_disciplina, nf.cod_turma, t.cod_curso, 
                      c.nome AS nome_curso,
                      nf.cod_disciplina, 
                      nf.situacao, 
                      nf.carga_horaria, 
                      CASE WHEN aae.cod_turma = nf.cod_turma THEN aae.descricao_atividade ELSE NULL END AS descricao_atividade_extra, 
                      CASE WHEN aae.cod_turma = nf.cod_turma THEN aae.data_atividade ELSE NULL END AS data_atividade_extra, 
                      CASE WHEN aae.cod_turma = nf.cod_turma THEN aae.carga_horaria ELSE NULL END AS carga_horaria_extra,
                      CASE WHEN aae.cod_turma = nf.cod_turma THEN aae.tipo_atividade ELSE NULL END AS tipo_atividade_extra
                FROM dbo.NotaFalta nf 
                JOIN dbo.Disciplina d ON nf.cod_disciplina = d.cod_disciplina 
                JOIN dbo.Turma t ON nf.cod_turma = t.cod_turma 
                JOIN dbo.Curso c ON t.cod_curso = c.cod_curso 
                INNER JOIN dbo.pessoa p ON nf.matricula_aluno = p.cod_pessoa 
                LEFT JOIN dbo.Aluno_AtividadesExtras aae ON nf.matricula_aluno = aae.matricula_aluno
                WHERE p.nome LIKE ?
                ORDER BY c.nome""",
            ['Matricula', 'Nome', 'Média Final', 'Nome Disciplina', 'Cod Turma', 'Cod Curso', 'Nome Curso', 'Cod Disciplina', 'Situação', 'Carga Horária', 'Descrição Atividade Extra', 'Data Atividade Extra', 'Carga Horária Extra', 'Tipo Atividade Extra']
        ),
        "Requerimento": (
            "SELECT DISTINCT pr.cod_pessoa, p.nome FROM LogGeo.Pessoa_Requerimento pr INNER JOIN dbo.pessoa p ON pr.cod_pessoa = p.cod_pessoa WHERE p.nome LIKE ? OR pr.cod_pessoa LIKE ?",
            "SELECT pr.cod_pessoa, p.nome, pr.cod_requerimento, r.descricao AS descricao_requerimento, "
            "pr.numero_protocolo, pr.data_requerimento, pr.status, pr.usuario, pr.chave, "
            "t.cod_turma, t.cod_curso, c.nome AS nome_curso, pr.data_previsao_entrega, "
            "pr.departamento AS departamento_principal, pr.tipo_log, pr.data_hora_log, "
            "pr.usuario_log, prd.data AS data_detalhe, prd.usuario AS usuario_detalhe, "
            "prd.departamento AS departamento_detalhe, prd.descricao AS descricao_detalhe, "
            "prd.status AS status_detalhe, prd.data_hora_log AS data_hora_log_detalhe, "
            "prd.usuario_log "
            "FROM LogGeo.Pessoa_Requerimento pr "
            "JOIN dbo.Requerimento r ON pr.cod_requerimento = r.cod_requerimento "
            "JOIN dbo.Turma t ON pr.cod_turma = t.cod_turma "
            "JOIN dbo.Curso c ON t.cod_curso = c.cod_curso "
            "JOIN LogGeo.Pessoa_Requerimento_Detalhe prd ON pr.chave = prd.chave_pessoa_requerimento "
            "INNER JOIN dbo.pessoa p ON pr.cod_pessoa = p.cod_pessoa "
            "WHERE pr.cod_pessoa = ? "
            "ORDER BY c.nome",
            "SELECT pr.cod_pessoa, p.nome, pr.cod_requerimento, r.descricao AS descricao_requerimento, "
            "pr.numero_protocolo, pr.data_requerimento, pr.status, pr.usuario, pr.chave, "
            "t.cod_turma, t.cod_curso, c.nome AS nome_curso, pr.data_previsao_entrega, "
            "pr.departamento AS departamento_principal, pr.tipo_log, pr.data_hora_log, "
            "pr.usuario_log, prd.data AS data_detalhe, prd.usuario AS usuario_detalhe, "
            "prd.departamento AS departamento_detalhe, prd.descricao AS descricao_detalhe, "
            "prd.status AS status_detalhe, prd.data_hora_log AS data_hora_log_detalhe, "
            "prd.usuario_log "
            "FROM LogGeo.Pessoa_Requerimento pr "
            "JOIN dbo.Requerimento r ON pr.cod_requerimento = r.cod_requerimento "
            "JOIN dbo.Turma t ON pr.cod_turma = t.cod_turma "
            "JOIN dbo.Curso c ON t.cod_curso = c.cod_curso "
            "JOIN LogGeo.Pessoa_Requerimento_Detalhe prd ON pr.chave = prd.chave_pessoa_requerimento "
            "INNER JOIN dbo.pessoa p ON pr.cod_pessoa = p.cod_pessoa "
            "WHERE p.nome LIKE ? "
            "ORDER BY c.nome",
            ['Matricula', 'Nome', 'Cod Requerimento', 'Descrição Requerimento', 'Número Protocolo', 'Data Requerimento', 'Status', 'Usuário', 'Chave', 'Cod Turma', 'Cod Curso', 'Nome Curso', 'Data Previsão Entrega', 'Departamento Principal', 'Tipo Log', 'Data Hora Log', 'Usuário Log', 'Data Detalhe', 'Usuário Detalhe', 'Departamento Detalhe', 'Descrição Detalhe', 'Status Detalhe', 'Data Hora Log Detalhe', 'Usuário Log']
        ),
        "Matricula": (
            "SELECT DISTINCT m.matricula_aluno, p.nome AS nome_aluno FROM dbo.matricula m JOIN dbo.pessoa p ON m.matricula_aluno = p.cod_pessoa WHERE p.nome LIKE ? OR m.matricula_aluno LIKE ?",
            "SELECT m.matricula_aluno, p.nome AS nome_aluno, m.cod_turma, t.cod_curso, c.nome AS nome_curso, m.situacao, em.desc_situacao, m.resultado_final, "
            "CASE WHEN m.resultado_final = 'T' THEN 'Trancado' WHEN m.resultado_final = 'AC' THEN 'Aulas Concluídas' WHEN m.resultado_final = 'A' THEN 'Aprovado' WHEN m.resultado_final = 'S' THEN 'Cancelado' WHEN m.resultado_final = 'AG' THEN 'Aguardando' WHEN m.resultado_final = 'TE' THEN 'Turma Encerrada' WHEN m.resultado_final = 'D' THEN 'Desistente' WHEN m.resultado_final = 'G' THEN 'Aguardando Solicitação' WHEN m.resultado_final = 'R' THEN 'Recuperação' when m.resultado_final = 'C' THEN 'Cursando' when m.resultado_final = 'M' THEN 'Matriculado' when m.resultado_final = 'B' THEN 'Bloq. DP’s' ELSE m.resultado_final END AS desc_resultado_final, m.data_matricula, m.data_situacao, m.situacao_complementar, m.representante, m.consultor, m.supervisor, m.data_cadastro, m.grade "
            "FROM dbo.matricula m "
            "JOIN dbo.pessoa p ON m.matricula_aluno = p.cod_pessoa "
            "JOIN dbo.turma t ON m.cod_turma = t.cod_turma "
            "JOIN dbo.curso c ON t.cod_curso = c.cod_curso "
            "LEFT JOIN (SELECT matricula_aluno, cod_turma, MAX(desc_situacao) AS desc_situacao FROM dbo.entity_Matricula GROUP BY matricula_aluno, cod_turma) em "
            "ON m.matricula_aluno = em.matricula_aluno AND m.cod_turma = em.cod_turma "
            "WHERE m.matricula_aluno = ? ",
            "SELECT m.matricula_aluno, p.nome AS nome_aluno, m.cod_turma, t.cod_curso, c.nome AS nome_curso, m.situacao, em.desc_situacao, m.resultado_final, "
            "CASE WHEN m.resultado_final = 'T' THEN 'Trancado' WHEN m.resultado_final = 'AC' THEN 'Aulas Concluídas' WHEN m.resultado_final = 'A' THEN 'Aprovado' WHEN m.resultado_final = 'S' THEN 'Cancelado' WHEN m.resultado_final = 'AG' THEN 'Aguardando' WHEN m.resultado_final = 'TE' THEN 'Turma Encerrada' WHEN m.resultado_final = 'D' THEN 'Desistente' WHEN m.resultado_final = 'G' THEN 'Aguardando Solicitação' WHEN m.resultado_final = 'R' THEN 'Recuperação' when m.resultado_final = 'C' THEN 'Cursando' when m.resultado_final = 'M' THEN 'Matriculado' when m.resultado_final = 'B' THEN 'Bloq. DP’s' ELSE m.resultado_final END AS desc_resultado_final, m.data_matricula, m.data_situacao, m.situacao_complementar, m.representante, m.consultor, m.supervisor, m.data_cadastro, m.grade "
            "FROM dbo.matricula m "
            "JOIN dbo.pessoa p ON m.matricula_aluno = p.cod_pessoa "
            "JOIN dbo.turma t ON m.cod_turma = t.cod_turma "
            "JOIN dbo.curso c ON t.cod_curso = c.cod_curso "
            "LEFT JOIN (SELECT matricula_aluno, cod_turma, MAX(desc_situacao) AS desc_situacao FROM dbo.entity_Matricula GROUP BY matricula_aluno, cod_turma) em "
            "ON m.matricula_aluno = em.matricula_aluno AND m.cod_turma = em.cod_turma "
            "WHERE p.nome LIKE ?",
            ['Matricula', 'Nome', 'Cod Turma', 'Cod Curso', 'Nome Curso', 'Situação', 'Descrição Situação', 'Resultado Final', 'Descrição Resultado Final', 'Data Matrícula', 'Data Situação', 'Situação Complementar', 'Representante', 'Consultor', 'Supervisor', 'Data Cadastro', 'Grade']
        ),
        "Ocorrencia Inserir": (
            "SELECT cod_pessoa, nome FROM dbo.pessoa WHERE nome LIKE ? OR cod_pessoa LIKE ?",
            "SELECT cod_pessoa, nome FROM dbo.pessoa WHERE cod_pessoa = ?",
            "SELECT cod_pessoa, nome FROM dbo.pessoa WHERE nome LIKE ?",
            ['Matricula', 'Nome']
        ),
        "Ocorrencia Novo": (
            "SELECT DISTINCT matricula_aluno, nome_aluno FROM dbo.ocorrencias_novo WHERE nome_aluno LIKE ? OR matricula_aluno LIKE ?",
            "SELECT matricula_aluno, nome_aluno, data, descricao_novo, tipo, usuario FROM dbo.ocorrencias_novo WHERE matricula_aluno = ? ORDER BY data DESC",
            "SELECT matricula_aluno, nome_aluno, data, descricao_novo, tipo, usuario FROM dbo.ocorrencias_novo WHERE nome_aluno LIKE ? ORDER BY data DESC",
            ['Matricula', 'Nome', 'Data', 'Descrição', 'Tipo', 'Usuário']
        )
    }

    if user == "admin":
        queries["Financeiro"] = (
            "SELECT cod_pessoa, nome FROM dbo.pessoa WHERE nome LIKE ? OR cod_pessoa LIKE ?",
            "SELECT cb.cod_pessoa, p.nome AS nome_pessoa, cb.cod_servico, cb.parcela, cb.status, c.nome AS nome_curso, t.cod_curso, FORMAT(cb.data_vencimento, 'dd/MM/yyyy') AS data_vencimento, cb.valor_bruto, cb.valor_desconto, cb.valor_pago,  cb.cod_turma, cb.status_cobranca "
            "FROM dbo.cobranca cb "
            "JOIN dbo.Turma t ON cb.cod_turma = t.cod_turma "
            "JOIN dbo.Curso c ON t.cod_curso = c.cod_curso "
            "JOIN dbo.Pessoa p ON cb.cod_pessoa = p.cod_pessoa "
            "WHERE cb.cod_pessoa = ? "
            "ORDER BY t.cod_turma, "
            "CASE WHEN CHARINDEX('/', cb.parcela) > 0 THEN CAST(SUBSTRING(cb.parcela, 1, CHARINDEX('/', cb.parcela) - 1) AS INT) ELSE 0 END ASC, "
            "CASE cb.status WHEN 'PG' THEN 0 ELSE 1 END",
            "SELECT cb.cod_pessoa, p.nome AS nome_pessoa, cb.cod_servico, cb.parcela, cb.status, c.nome AS nome_curso, t.cod_curso, FORMAT(cb.data_vencimento, 'dd/MM/yyyy') AS data_vencimento, cb.valor_bruto, cb.valor_desconto, cb.valor_pago,  cb.cod_turma, cb.status_cobranca "
            "FROM dbo.cobranca cb "
            "JOIN dbo.Turma t ON cb.cod_turma = t.cod_turma "
            "JOIN dbo.Curso c ON t.cod_curso = c.cod_curso "
            "JOIN dbo.Pessoa p ON cb.cod_pessoa = p.cod_pessoa "
            "WHERE p.nome LIKE ? "
            "ORDER BY t.cod_turma, "
            "CASE WHEN CHARINDEX('/', cb.parcela) > 0 THEN CAST(SUBSTRING(cb.parcela, 1, CHARINDEX('/', cb.parcela) - 1) AS INT) ELSE 0 END ASC, "
            "CASE cb.status WHEN 'PG' THEN 0 ELSE 1 END",
            ['Matricula', 'Nome', 'Cod Serviço', 'Parcela', 'Status', 'Nome Curso', 'Cod Curso', 'Valor Desconto', 'Valor Pago', 'Cod Turma', 'Valor Bruto', 'Data Vencimento', 'Status Cobrança']
        )
    
    for key in queries.keys():
        current_page[key] = 1
        current_col_start[key] = 0

    # Ajustando as queries de relatório, incluindo telefone no Cursos
    relatorios_queries = {
        "Representante": (
            "SELECT p.nome, p.celular AS Telefone, c.nome AS Curso FROM dbo.matricula m JOIN dbo.pessoa p ON m.matricula_aluno = p.cod_pessoa JOIN dbo.turma t ON m.cod_turma = t.cod_turma JOIN dbo.curso c ON t.cod_curso = c.cod_curso WHERE m.representante LIKE ?",
            "SELECT p.nome, p.celular AS Telefone, c.nome AS Curso FROM dbo.matricula m JOIN dbo.pessoa p ON m.matricula_aluno = p.cod_pessoa JOIN dbo.turma t ON m.cod_turma = t.cod_turma JOIN dbo.curso c ON t.cod_curso = c.cod_curso WHERE m.representante = ?",
            "SELECT p.nome, p.celular AS Telefone, c.nome AS Curso FROM dbo.matricula m JOIN dbo.pessoa p ON m.matricula_aluno = p.cod_pessoa JOIN dbo.turma t ON m.cod_turma = t.cod_turma JOIN dbo.curso c ON t.cod_curso = c.cod_curso WHERE m.representante LIKE ?",
            ['Nome', 'Telefone', 'Curso']
        ),
        "Cursos": (
            "SELECT p.nome AS NomeCliente, p.celular AS Telefone, c.nome AS Curso FROM dbo.matricula m JOIN dbo.pessoa p ON m.matricula_aluno = p.cod_pessoa JOIN dbo.turma t ON m.cod_turma = t.cod_turma JOIN dbo.curso c ON t.cod_curso = c.cod_curso WHERE c.nome LIKE ?",
            "SELECT p.nome AS NomeCliente, p.celular AS Telefone, c.nome AS Curso FROM dbo.matricula m JOIN dbo.pessoa p ON m.matricula_aluno = p.cod_pessoa JOIN dbo.turma t ON m.cod_turma = t.cod_turma JOIN dbo.curso c ON t.cod_curso = c.cod_curso WHERE c.nome = ?",
            "SELECT p.nome AS NomeCliente, p.celular AS Telefone, c.nome AS Curso FROM dbo.matricula m JOIN dbo.pessoa p ON m.matricula_aluno = p.cod_pessoa JOIN dbo.turma t ON m.cod_turma = t.cod_turma JOIN dbo.curso c ON t.cod_curso = c.cod_curso WHERE c.nome LIKE ?",
            ['NomeCliente', 'Telefone', 'Curso']
        )
    }

    relatorio_resultados = []
    modo_exportacao = "pdf"
    report_type = "Representante"

    def copy_to_clipboard(value):
        page.set_clipboard(value)
        page.snack_bar = ft.SnackBar(ft.Text("Texto copiado com sucesso!"))
        page.snack_bar.open = True
        page.update()

    def show_popup(text):
        def close_popup(e):
            page.dialog.open = False
            page.update()

        page.dialog = ft.AlertDialog(
            title=ft.Text("Observação"),
            content=ft.Text(text),
            actions=[ft.TextButton("Fechar", on_click=close_popup)],
            on_dismiss=lambda e: close_popup(None)
        )
        page.dialog.open = True
        page.update()

    def select_suggestion(value, name, tab_key):
        search_fields[tab_key].value = value
        if tab_key == "Ocorrencia Inserir":
            matricula_field.value = value
            nome_field.value = name
            data_field.value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        suggestion_lists[tab_key].visible = False
        page.update()
        if tab_key != "Ocorrencia Inserir":
            threading.Thread(target=execute_search, args=(value, tab_key)).start()

    def execute_search(value, tab_key):
        value = str(value)
        if value.isdigit():
            query = queries[tab_key][1]
            params = (value,)
        else:
            query = queries[tab_key][2]
            params = (f'%{value}%',)

        if tab_key in loading_indicators:
            loading_indicators[tab_key].visible = True
        page.update()

        results = search_database(query, params)

        if tab_key in loading_indicators:
            loading_indicators[tab_key].visible = False
        if results:
            if tab_key != "Ocorrencia Inserir":
                paginate_results(results, tab_key)
            elif tab_key == "Ocorrencia Inserir":
                if len(results) == 1:
                    select_suggestion(results[0][0], results[0][1], tab_key)
        else:
            page.snack_bar = ft.SnackBar(ft.Text(f"Resultado não encontrado em {tab_key}"))
            page.snack_bar.open = True
        page.update()
        return results

    def fetch_suggestions(tab_key):
        query = queries[tab_key][0]
        params = (f'%{search_fields[tab_key].value}%', f'%{search_fields[tab_key].value}%')
        results = search_database(query, params)
        suggestion_lists[tab_key].controls.clear()
        for row in results[:10]:
            suggestion_lists[tab_key].controls.append(ft.TextButton(
                text=f"{row[0]} - {row[1]}",
                on_click=lambda e, val=row[0], name=row[1]: select_suggestion(val, name, tab_key)
            ))
        suggestion_lists[tab_key].visible = True
        page.update()

    def show_suggestions(e, tab_key):
        threading.Thread(target=fetch_suggestions, args=(tab_key,)).start()

    def search(e, tab_key, search_all=False):
        if search_all:
            search_value = search_fields[tab_key].value
            for k in queries.keys():
                if k != "Ocorrencia Inserir":
                    threading.Thread(target=execute_search, args=(search_value, k)).start()
        else:
            threading.Thread(target=execute_search, args=(search_fields[tab_key].value, tab_key)).start()

    def clear_search(tab_key=None):
        for key in search_fields.keys():
            if key in ["Ocorrencia Inserir", "Ocorrencia Novo"]:
                continue
            search_fields[key].value = ""
            suggestion_lists[key].controls.clear()
            suggestion_lists[key].visible = False
            data_tables[key].rows.clear()
            pagination_container[key].controls.clear()
            column_container[key].controls.clear()
        page.update()

    def paginate_results(results, tab_key):
        data_tables[tab_key].rows.clear()
        total_pages = (len(results) + page_size - 1) // page_size
        current_page[tab_key] = 1

        def display_page(page_number):
            data_tables[tab_key].rows.clear()
            start_index = (page_number - 1) * page_size
            end_index = min(start_index + page_size, len(results))
            display_columns = queries[tab_key][3][current_col_start[tab_key]:current_col_start[tab_key] + columns_per_page]
            data_tables[tab_key].columns.clear()
            data_tables[tab_key].columns.extend([ft.DataColumn(ft.Text(col, color=ft.Colors.BLACK)) for col in display_columns])

            observacao_col_index = queries[tab_key][3].index('Descrição Observação') if 'Descrição Observação' in queries[tab_key][3] else -1
            certificado_col_index = queries[tab_key][3].index('Observação') if 'Observação' in queries[tab_key][3] else -1
            descricao_requerimento_col_index = queries[tab_key][3].index('Descrição Requerimento') if 'Descrição Requerimento' in queries[tab_key][3] else -1
            descricao_detalhe_col_index = queries[tab_key][3].index('Descrição Detalhe') if 'Descrição Detalhe' in queries[tab_key][3] else -1
            nome_disciplina_col_index = queries[tab_key][3].index('Nome Disciplina') if 'Nome Disciplina' in queries[tab_key][3] else -1
            nome_curso_col_index = queries[tab_key][3].index('Nome Curso') if 'Nome Curso' in queries[tab_key][3] else -1
            descricao_col_index = queries[tab_key][3].index('Descrição') if 'Descrição' in queries[tab_key][3] else -1
            descricao_novo_col_index = queries[tab_key][3].index('Descrição Novo') if 'Descrição Novo' in queries[tab_key][3] else -1
            descricao_atividade_extra_col_index = queries[tab_key][3].index('Descrição Atividade Extra') if 'Descrição Atividade Extra' in queries[tab_key][3] else -1

            nome_col_index = queries[tab_key][3].index('Nome') if 'Nome' in queries[tab_key][3] else -1
            cpf_col_index = queries[tab_key][3].index('CPF/CNPJ') if 'CPF/CNPJ' in queries[tab_key][3] else -1
            email_col_index = queries[tab_key][3].index('Email') if 'Email' in queries[tab_key][3] else -1
            celular_col_index = queries[tab_key][3].index('Celular') if 'Celular' in queries[tab_key][3] else -1

            for row in results[start_index:end_index]:
                row_cells = []
                for i in range(current_col_start[tab_key], min(current_col_start[tab_key] + columns_per_page, len(row))):
                    if i in [nome_col_index, cpf_col_index, email_col_index, celular_col_index]:
                        cell_content = ft.Row([
                            ft.Text(f"{row[i]}", color=ft.Colors.BLACK, expand=True, text_align=ft.TextAlign.LEFT, width=200, height=40),
                            ft.IconButton(ft.Icons.COPY, on_click=lambda e, val=row[i]: copy_to_clipboard(val), icon_color=ft.Colors.BLACK)
                        ])
                    elif i in [observacao_col_index, certificado_col_index, descricao_requerimento_col_index, descricao_detalhe_col_index, nome_disciplina_col_index, nome_curso_col_index, descricao_col_index, descricao_novo_col_index, descricao_atividade_extra_col_index]:
                        cell_content = ft.Row([
                            ft.Text(f"{row[i]}", color=ft.Colors.BLACK, expand=True, text_align=ft.TextAlign.LEFT, width=200, height=40),
                            ft.IconButton(ft.Icons.INFO, on_click=lambda e, val=row[i]: show_popup(val), icon_color=ft.Colors.BLACK)
                        ])
                    else:
                        cell_content = ft.Text(f"{row[i]}", color=ft.Colors.BLACK, expand=True, text_align=ft.TextAlign.LEFT, width=200, height=40)
                    row_cells.append(ft.DataCell(cell_content))
                data_tables[tab_key].rows.append(ft.DataRow(cells=row_cells))
            update_column_navigation_text(tab_key)
            update_pagination_text(tab_key, total_pages)
            page.update()

        def next_page(e):
            if current_page[tab_key] < total_pages:
                current_page[tab_key] += 1
                display_page(current_page[tab_key])

        def prev_page(e):
            if current_page[tab_key] > 1:
                current_page[tab_key] -= 1
                display_page(current_page[tab_key])

        def next_column(e):
            if current_col_start[tab_key] + columns_per_page < len(queries[tab_key][3]):
                current_col_start[tab_key] += columns_per_page
                display_page(current_page[tab_key])

        def prev_column(e):
            if current_col_start[tab_key] > 0:
                current_col_start[tab_key] -= columns_per_page
                display_page(current_page[tab_key])

        def update_column_navigation_text(tab_key):
            column_navigation_text[tab_key].value = f"Colunas(Lado) {current_col_start[tab_key] + 1}-{min(current_col_start[tab_key] + columns_per_page, len(queries[tab_key][3]))} de {len(queries[tab_key][3])}"
            column_navigation_text[tab_key].color = ft.Colors.BLACK
        
        def update_pagination_text(tab_key, total_pages):
            pagination_text[tab_key].value = f"Página (Baixo) {current_page[tab_key]} de {total_pages}"
            pagination_text[tab_key].color = ft.Colors.BLACK

        pagination_text[tab_key] = ft.Text(color=ft.Colors.BLACK)
        pagination_controls = ft.Row(
            [
                ft.IconButton(ft.Icons.ARROW_UPWARD, on_click=prev_page, icon_color=ft.Colors.BLACK),
                pagination_text[tab_key],
                ft.IconButton(ft.Icons.ARROW_DOWNWARD, on_click=next_page, icon_color=ft.Colors.BLACK)
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )

        column_navigation_text[tab_key] = ft.Text(f"Colunas {current_col_start[tab_key] + 1}-{min(current_col_start[tab_key] + columns_per_page, len(queries[tab_key][3]))} de {len(queries[tab_key][3])}", color=ft.Colors.BLACK)
        column_navigation_controls = ft.Row(
            [
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=prev_column, icon_color=ft.Colors.BLACK),
                column_navigation_text[tab_key],
                ft.IconButton(ft.Icons.ARROW_FORWARD, on_click=next_column, icon_color=ft.Colors.BLACK)
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )

        display_page(current_page[tab_key])
        pagination_container[tab_key].controls.clear()
        pagination_container[tab_key].controls.append(pagination_controls)
        column_container[tab_key].controls.clear()
        column_container[tab_key].controls.append(column_navigation_controls)
        page.update()

    def create_tab_content(tab_key):
        search_field = ft.TextField(
            hint_text="Buscar",
            hint_style=ft.TextStyle(color="#982938"),
            expand=True,
            border_color="#982938",
            border_radius=20,
            content_padding=ft.padding.symmetric(vertical=10, horizontal=10),
            text_align=ft.TextAlign.LEFT,
            color=ft.Colors.BLACK,
            cursor_color=ft.Colors.BLACK,
            on_change=lambda e: show_suggestions(e, tab_key),
            on_submit=lambda e: search(e, tab_key)
        )
        search_fields[tab_key] = search_field

        search_button = ft.ElevatedButton(
            text="BUSCAR",
            color=ft.Colors.WHITE,
            bgcolor="#982938",
            on_click=lambda e: search(e, tab_key, search_all=False),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
            height=50
        )

        search_all_button = ft.ElevatedButton(
            text="BUSCAR TUDO",
            color=ft.Colors.WHITE,
            bgcolor="#982938",
            on_click=lambda e: search(e, tab_key, search_all=True),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
            height=50
        )
      
        clear_button = ft.ElevatedButton(
            text="LIMPAR",
            color=ft.Colors.WHITE,
            bgcolor="#982938",
            on_click=lambda e: clear_search(tab_key),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
            height=50
        )

        data_table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(col, color=ft.Colors.BLACK)) for col in queries[tab_key][3][:columns_per_page]],
            rows=[],
            column_spacing=10,
            heading_row_color=ft.Colors.GREY_200,
            data_row_color=ft.Colors.GREY_100,
            border=ft.Border(
                left=ft.BorderSide(color="#D4D4D4", width=1),
                top=ft.BorderSide(color="#D4D4D4", width=1),
                right=ft.BorderSide(color="#D4D4D4", width=1),
                bottom=ft.BorderSide(color="#D4D4D4", width=1),
            ),
            heading_text_style=ft.TextStyle(color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD),
            data_text_style=ft.TextStyle(color=ft.Colors.BLACK),
            expand=True
        )
        data_tables[tab_key] = data_table

        suggestion_list = ft.ListView(expand=False, visible=False, height=200)
        suggestion_lists[tab_key] = suggestion_list

        pagination_controls = ft.Column()
        pagination_container[tab_key] = pagination_controls

        column_controls = ft.Column()
        column_container[tab_key] = column_controls

        loading_indicator = ft.ProgressBar(width=20, visible=False, bgcolor=ft.Colors.GREY_400)
        loading_indicators[tab_key] = loading_indicator

        return ft.Column(
            [
                ft.Row(
                    [
                        search_field,
                        loading_indicator,
                        ft.Container(content=search_button, alignment=ft.alignment.center, margin=ft.margin.only(right=10)),
                        ft.Container(content=search_all_button, alignment=ft.alignment.center, margin=ft.margin.only(right=10)),
                        ft.Container(content=clear_button, alignment=ft.alignment.center, margin=ft.margin.only(right=10)),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                suggestion_list,
                data_table,
                pagination_controls,
                column_controls
            ],
            spacing=20,
            expand=True
        )

    def create_ocorrencia_inserir_tab():
        global matricula_field, nome_field, data_field

        search_field = ft.TextField(
            hint_text="Buscar Pessoa",
            hint_style=ft.TextStyle(color="#982938"),
            expand=True,
            border_color="#982938",
            border_radius=20,
            content_padding=ft.padding.symmetric(vertical=10, horizontal=10),
            text_align=ft.TextAlign.LEFT,
            color=ft.Colors.BLACK,
            cursor_color=ft.Colors.BLACK,
            on_change=lambda e: show_suggestions(e, "Ocorrencia Inserir"),
            on_submit=lambda e: search(e, "Ocorrencia Inserir")
        )
        search_fields["Ocorrencia Inserir"] = search_field

        search_button = ft.ElevatedButton(
            text="Buscar",
            color=ft.Colors.WHITE,
            bgcolor="#982938",
            on_click=lambda e: search(e, "Ocorrencia Inserir"),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
            height=50
        )

        suggestion_list = ft.ListView(expand=False, visible=False, height=200)
        suggestion_lists["Ocorrencia Inserir"] = suggestion_list

        matricula_field = ft.TextField(label="Matricula", read_only=True, color=ft.Colors.BLACK)
        nome_field = ft.TextField(label="Nome", read_only=True, color=ft.Colors.BLACK)
        data_field = ft.TextField(label="Data e Hora", read_only=True, color=ft.Colors.BLACK)
        descricao_field = ft.TextField(label="Descrição", color=ft.Colors.BLACK)
        tipo_field = ft.TextField(label="Tipo", color=ft.Colors.BLACK)
        usuario_field = ft.TextField(label="Usuário", color=ft.Colors.BLACK)

        def inserir_ocorrencia(e):
            matricula = matricula_field.value
            nome = nome_field.value
            data = data_field.value
            descricao = descricao_field.value
            tipo = tipo_field.value
            usuario = usuario_field.value

            if insert_ocorrencia(matricula, nome, data, descricao, tipo, usuario):
                snack_bar = ft.SnackBar(ft.Text("Ocorrência inserida com sucesso!"))
                matricula_field.value = ""
                nome_field.value = ""
                data_field.value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                descricao_field.value = ""
                tipo_field.value = ""
                usuario_field.value = ""
            else:
                snack_bar = ft.SnackBar(ft.Text("Erro ao inserir ocorrência!"))
            
            page.overlay.append(snack_bar)
            snack_bar.open = True
            page.update()

        inserir_button = ft.ElevatedButton(
            text="INSERIR",
            color=ft.Colors.WHITE,
            bgcolor="#982938",
            on_click=inserir_ocorrencia,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
            height=50
        )

        loading_indicator = ft.ProgressBar(width=20, visible=False, bgcolor=ft.Colors.GREY_400)
        loading_indicators["Ocorrencia Inserir"] = loading_indicator

        return ft.Column(
            [
                ft.Row(
                    [
                        search_field,
                        search_button,
                        loading_indicator,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                suggestion_list,
                matricula_field,
                nome_field,
                data_field,
                descricao_field,
                tipo_field,
                usuario_field,
                inserir_button
            ],
            spacing=20,
            expand=True
        )

    def create_ocorrencia_novo_tab():
        search_field = ft.TextField(
            hint_text="Buscar Ocorrência",
            hint_style=ft.TextStyle(color="#982938"),
            expand=True,
            border_color="#982938",
            border_radius=20,
            content_padding=ft.padding.symmetric(vertical=10, horizontal=10),
            text_align=ft.TextAlign.LEFT,
            color=ft.Colors.BLACK,
            cursor_color=ft.Colors.BLACK,
            on_change=lambda e: show_suggestions(e, "Ocorrencia Novo"),
            on_submit=lambda e: search(e, "Ocorrencia Novo")
        )
        search_fields["Ocorrencia Novo"] = search_field

        search_button = ft.ElevatedButton(
            text="BUSCAR",
            color=ft.Colors.WHITE,
            bgcolor="#982938",
            on_click=lambda e: search(e, "Ocorrencia Novo"),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
            height=50
        )

        data_table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(col, color=ft.Colors.BLACK)) for col in queries["Ocorrencia Novo"][3][:columns_per_page]],
            rows=[],
            column_spacing=10,
            heading_row_color=ft.Colors.GREY_200,
            data_row_color=ft.Colors.GREY_100,
            border=ft.Border(
                left=ft.BorderSide(color="#D4D4D4", width=1),
                top=ft.BorderSide(color="#D4D4D4", width=1),
                right=ft.BorderSide(color="#D4D4D4", width=1),
                bottom=ft.BorderSide(color="#D4D4D4", width=1),
            ),
            heading_text_style=ft.TextStyle(color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD),
            data_text_style=ft.TextStyle(color=ft.Colors.BLACK),
            expand=True
        )
        data_tables["Ocorrencia Novo"] = data_table

        suggestion_list = ft.ListView(expand=False, visible=False, height=200)
        suggestion_lists["Ocorrencia Novo"] = suggestion_list

        pagination_controls = ft.Column()
        pagination_container["Ocorrencia Novo"] = pagination_controls

        column_controls = ft.Column()
        column_container["Ocorrencia Novo"] = column_controls

        loading_indicator = ft.ProgressBar(width=20, visible=False, bgcolor=ft.Colors.GREY_400)
        loading_indicators["Ocorrencia Novo"] = loading_indicator

        return ft.Column(
            [
                ft.Row(
                    [
                        search_field,
                        loading_indicator,
                        ft.Container(content=search_button, alignment=ft.alignment.center, margin=ft.margin.only(right=10))
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                suggestion_list,
                data_table,
                pagination_controls,
                column_controls
            ],
            spacing=20,
            expand=True
        )

    def carregar_representantes():
        q = "SELECT DISTINCT representante FROM dbo.matricula WHERE representante IS NOT NULL AND representante <> ''"
        resultados = search_database(q, ())
        return [r[0] for r in resultados if r[0]]

    def carregar_cursos():
        q = "SELECT DISTINCT c.nome FROM dbo.matricula m JOIN dbo.turma t ON m.cod_turma=t.cod_turma JOIN dbo.curso c ON t.cod_curso=c.cod_curso"
        resultados = search_database(q, ())
        return [r[0] for r in resultados if r[0]]

    for tab_key in queries.keys():
        if tab_key != "Ocorrencia Inserir":
            tabs[tab_key] = create_tab_content(tab_key)

    def create_relatorios_tab():
        nonlocal relatorio_resultados, modo_exportacao, report_type, relatorios_queries
        report_type_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option("Representante"), ft.dropdown.Option("Cursos")],
            value="Representante",
            width=200,
            border_color="#982938",
            color=ft.Colors.BLACK,
        )

        secondary_dropdown = ft.Dropdown(
            options=[],
            width=300,
            border_color="#982938",
            color=ft.Colors.BLACK,
        )

        def atualizar_opcoes(e):
            nonlocal report_type
            report_type = report_type_dropdown.value
            if report_type == "Representante":
                reps = carregar_representantes()
                secondary_dropdown.options = [ft.dropdown.Option(rep) for rep in reps]
                secondary_dropdown.value = reps[0] if reps else None
            else:
                cursos = carregar_cursos()
                secondary_dropdown.options = [ft.dropdown.Option(c) for c in cursos]
                secondary_dropdown.value = cursos[0] if cursos else None
            page.update()

        report_type_dropdown.on_change = atualizar_opcoes
        atualizar_opcoes(None)

        data_table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(" ", color=ft.Colors.BLACK))],
            rows=[],
            column_spacing=10,
            heading_row_color=ft.Colors.GREY_200,
            data_row_color=ft.Colors.GREY_100,
            border=ft.Border(
                left=ft.BorderSide(color="#D4D4D4", width=1),
                top=ft.BorderSide(color="#D4D4D4", width=1),
                right=ft.BorderSide(color="#D4D4D4", width=1),
                bottom=ft.BorderSide(color="#D4D4D4", width=1),
            ),
            heading_text_style=ft.TextStyle(color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD),
            data_text_style=ft.TextStyle(color=ft.Colors.BLACK),
            expand=True
        )

        loading_indicator = ft.ProgressBar(width=20, visible=False, bgcolor=ft.Colors.GREY_400)

        def run_report(e):
            nonlocal relatorio_resultados, report_type
            loading_indicator.visible = True
            page.update()

            rtype = report_type
            valor = secondary_dropdown.value
            q = relatorios_queries[rtype]

            query = q[1]
            params = (valor,)

            results = search_database(query, params)

            loading_indicator.visible = False
            data_table.rows.clear()
            data_table.columns.clear()

            if results:
                relatorio_resultados.clear()
                relatorio_resultados.extend(results)

                for col in q[3]:
                    data_table.columns.append(ft.DataColumn(ft.Text(col, color=ft.Colors.BLACK)))

                for row in results:
                    cells = [ft.DataCell(ft.Row([ft.Text(str(cell_value), color=ft.Colors.BLACK, expand=True)])) for cell_value in row]
                    data_table.rows.append(ft.DataRow(cells=cells))
            else:
                page.overlay.append(ft.SnackBar(ft.Text("Nenhum resultado encontrado!")))
                page.overlay[-1].open = True

            page.update()

        file_picker_save = ft.FilePicker()
        page.overlay.append(file_picker_save)

        def salvar_arquivo(e: ft.FilePickerResultEvent):
            nonlocal relatorio_resultados, modo_exportacao, report_type, relatorios_queries
            if e.path is not None and relatorio_resultados:
                rtype = report_type
                if modo_exportacao == "pdf":
                    if not e.path.lower().endswith(".pdf"):
                        e.path += ".pdf"
                    c = canvas.Canvas(e.path)
                    colunas = relatorios_queries[rtype][3]
                    y = 800
                    c.drawString(50, y, "Relatório - " + rtype)
                    y -= 20
                    c.drawString(50, y, " | ".join(colunas))
                    y -= 20
                    for row in relatorio_resultados:
                        linha = " | ".join(str(item) for item in row)
                        c.drawString(50, y, linha)
                        y -= 20
                        if y < 50:
                            c.showPage()
                            y = 800
                    c.save()
                    page.overlay.append(ft.SnackBar(ft.Text("Arquivo PDF salvo com sucesso!")))
                elif modo_exportacao == "csv":
                    if not e.path.lower().endswith(".csv"):
                        e.path += ".csv"
                    with open(e.path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f, delimiter=';')
                        writer.writerow(relatorios_queries[rtype][3])
                        for linha in relatorio_resultados:
                            writer.writerow(linha)
                    page.overlay.append(ft.SnackBar(ft.Text("Arquivo CSV salvo com sucesso!")))

                page.overlay[-1].open = True
                page.update()
            else:
                page.overlay.append(ft.SnackBar(ft.Text("Nenhum dado para exportar!")))
                page.overlay[-1].open = True
                page.update()

        file_picker_save.on_result = salvar_arquivo

        def download_pdf(e):
            nonlocal modo_exportacao
            modo_exportacao = "pdf"
            file_picker_save.save_file(file_name="relatorio.pdf")

        def download_csv(e):
            nonlocal modo_exportacao
            modo_exportacao = "csv"
            file_picker_save.save_file(file_name="relatorio.csv")

        search_button = ft.ElevatedButton(
            text="GERAR RELATÓRIO",
            color=ft.Colors.WHITE,
            bgcolor="#982938",
            on_click=run_report,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
            height=50
        )

        # Adicionado botão de CSV
        download_pdf_button = ft.ElevatedButton(
            text="BAIXAR PDF",
            color=ft.Colors.WHITE,
            bgcolor="#982938",
            on_click=download_pdf,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
            height=50
        )

        download_csv_button = ft.ElevatedButton(
            text="BAIXAR CSV",
            color=ft.Colors.WHITE,
            bgcolor="#982938",
            on_click=download_csv,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
            height=50
        )

        return ft.Column(
            [
                ft.Row(
                    [
                        report_type_dropdown,
                        secondary_dropdown,
                        loading_indicator,
                        search_button,
                        download_pdf_button,
                        download_csv_button
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                data_table
            ],
            spacing=20,
            expand=True
        )

    relatorios_tab = create_relatorios_tab()

    page.add(
        ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Pessoa", content=tabs["Pessoa"]),
                ft.Tab(text="Documento", content=tabs["Documento"]),
                ft.Tab(text="Certificado", content=tabs["Certificado"]),
                ft.Tab(text="Ocorrencia", content=tabs["Ocorrencia"]),
                ft.Tab(text="Nota/Falta", content=tabs["Nota/Falta"]),
                ft.Tab(text="Requerimento", content=tabs["Requerimento"]),
                ft.Tab(text="Matricula", content=tabs["Matricula"]),
                ft.Tab(text="Ocorrencia Inserir", content=create_ocorrencia_inserir_tab()),
                ft.Tab(text="Ocorrencia Novo", content=create_ocorrencia_novo_tab()),
                *( [ft.Tab(text="Financeiro", content=create_tab_content("Financeiro"))] if user == "admin" else [] ),
                ft.Tab(text="Relatorios", content=relatorios_tab)
            ],
            indicator_color="#982938",
            label_color="#982938",
            unselected_label_color=ft.Colors.GREY_600,
            expand=True
        )
    )

    direitos_reservados = add_direitos_reservados()
    page.add(direitos_reservados)
    page.update()

def login(page: ft.Page):
    def toggle_password_visibility(e):
        password.password = not password.password
        eye_button.icon = ft.Icons.VISIBILITY_OFF if password.password else ft.Icons.VISIBILITY
        page.update()

    def try_login(e):
        user = username.value
        pwd = password.value
        if user == "tca" and pwd == "iteq@2025!!":
            page.clean()
            app_main(page, "user")
        elif user == "tcaf" and pwd == "iteq@2025":
            page.clean()
            app_main(page, "admin")
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Credenciais inválidas!"))
            page.snack_bar.open = True
            page.update()

    page.title = "TCA"
    page.bgcolor = ft.Colors.GREY_200
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    username = ft.TextField(
        label="",
        hint_text="Usuário",
        prefix=ft.Icon(name=ft.Icons.PERSON, color="#982938"),
        width=250,
        border_color="#982938",
        border_radius=20,
        content_padding=ft.padding.symmetric(vertical=10, horizontal=10),
        text_align=ft.TextAlign.LEFT,
        hint_style=ft.TextStyle(color="#982938"),
        color="#982938",
        cursor_color="#982938"
    )

    eye_button = ft.IconButton(
        icon=ft.Icons.VISIBILITY,
        icon_color="#982938",
        on_click=toggle_password_visibility,
        width=30,
        height=30,
        padding=ft.padding.all(5)
    )

    password = ft.TextField(
        label="",
        hint_text="Senha",
        prefix=ft.Icon(name=ft.Icons.LOCK, color="#982938"),
        suffix=eye_button,
        width=250,
        border_color="#982938",
        border_radius=20,
        content_padding=ft.padding.symmetric(vertical=10, horizontal=10),
        text_align=ft.TextAlign.LEFT,
        password=True,
        hint_style=ft.TextStyle(color="#982938"),
        color="#982938",
        cursor_color="#982938"
    )

    login_button = ft.ElevatedButton(
        text="ENTRAR",
        color=ft.Colors.WHITE,
        bgcolor="#982938",
        width=250,
        height=45,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
        on_click=try_login
    )

    login_form = ft.Container(
        content=ft.Column(
            [
                username,
                password,
                login_button
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        ),
        padding=20,
        bgcolor=ft.Colors.GREY_300,
        border=ft.Border(
            left=ft.BorderSide(color="#982938", width=2),
            top=ft.BorderSide(color="#982938", width=2),
            right=ft.BorderSide(color="#982938", width=2),
            bottom=ft.BorderSide(color="#982938", width=2),
        ),
        border_radius=20,
        width=300,
        height=300
    )

    direitos_reservados = add_direitos_reservados()

    page.add(
        ft.Column(
            [
                ft.Container(
                    content=login_form,
                    alignment=ft.alignment.center,
                    margin=ft.margin.symmetric(horizontal=50),
                    expand=True
                ),
                direitos_reservados
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
    )

ft.app(target=login)

