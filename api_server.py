import pyodbc
import threading
import logging
from queue import Queue
from datetime import datetime, date
import io
import csv
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
# --- MUDANÇA: Imports de Autenticação Atualizados ---
# 'verify_jwt_in_request' e 'wraps' não são mais necessários
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required, JWTManager
from werkzeug.security import check_password_hash, generate_password_hash 
# --- FIM DA MUDANÇA ---

# --- Configuração do Logging ---
logging.basicConfig(level=logging.DEBUG)

# --- Lógica de Conexão (Sem alteração) ---
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
    logging.info(f"Pool de {tamanho_pool} conexões criado.")
    return pool

pool_conexoes = criar_pool_conexoes(20)

def search_database(query, params):
    conexao = pool_conexoes.get()
    if not conexao:
        logging.error("Não foi possível obter conexão do pool.")
        return []
    try:
        cursor = conexao.cursor()
        logging.debug(f"Executando Query: {query} com Params: {params}")
        cursor.execute(query, params)
        
        columns = [column[0] for column in cursor.description]
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
            
        logging.debug(f"Query retornou {len(results)} resultados.")
        return results
    except Exception as e:
        logging.error(f"Erro ao buscar dados: {e}")
        return []
    finally:
        pool_conexoes.put(conexao)

# --- Função de INSERT (Sem alteração) ---
def execute_insert(query, params):
    conexao = pool_conexoes.get()
    if not conexao:
        logging.error("Não foi possível obter conexão do pool para INSERT.")
        return False
    try:
        cursor = conexao.cursor()
        logging.debug(f"Executando INSERT: {query} com Params: {params}")
        cursor.execute(query, params)
        conexao.commit()
        logging.info("INSERT executado com sucesso.")
        return True
    except Exception as e:
        logging.error(f"Erro ao executar INSERT: {e}")
        conexao.rollback()
        return False
    finally:
        pool_conexoes.put(conexao)


# --- Dicionário de Queries (Seu código original, 100% intacto) ---
queries = {
    "Pessoa": (
        # 1. suggest_query (nome, matricula)
        "SELECT cod_pessoa, nome FROM dbo.pessoa WHERE nome LIKE ? OR cod_pessoa LIKE ?", 
        # 2. id_query (matricula)
        "SELECT cod_pessoa, nome, Sexo, endereco_residencial, bairro_residencial, cidade_residencial, estado_residencial, cep_residencial, fone_residencial, celular, email, rg, cpf_cnpj, nascimento_data FROM dbo.pessoa WHERE cod_pessoa = ?",
        # 3. name_query (nome)
        "SELECT cod_pessoa, nome, Sexo, endereco_residencial, bairro_residencial, cidade_residencial, estado_residencial, cep_residencial, fone_residencial, celular, email, rg, cpf_cnpj, nascimento_data FROM dbo.pessoa WHERE nome LIKE ?",
        # 4. cpf_query (cpf)
        "SELECT cod_pessoa, nome, Sexo, endereco_residencial, bairro_residencial, cidade_residencial, estado_residencial, cep_residencial, fone_residencial, celular, email, rg, cpf_cnpj, nascimento_data FROM dbo.pessoa WHERE cpf_cnpj LIKE ?", 
        # 5. columns
        ['Matricula', 'Nome', 'Sexo', 'Endereço', 'Bairro', 'Cidade', 'Estado', 'CEP', 'Telefone Residencial', 'Celular', 'Email', 'RG', 'CPF/CNPJ', 'Nascimento']
    ),
    "Documento": (
        # 1. suggest_query
        "SELECT DISTINCT pd.cod_pessoa, p.nome AS nome_pessoa FROM dbo.PessoaDocumento pd INNER JOIN dbo.pessoa p ON pd.cod_pessoa = p.cod_pessoa WHERE p.nome LIKE ? OR pd.cod_pessoa LIKE ?",
        # 2. id_query (matricula)
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
        # 3. name_query (nome)
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
        # 4. cpf_query (cpf)
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
            WHERE p.cpf_cnpj LIKE ? 
            ORDER BY pd.data_entrega ASC""",
        # 5. columns
        ['Matricula', 'Nome', 'Código Documento', 'Nome Documento', 'Status', 'Data Entrega']
    ),
    "Certificado": (
        # 1. suggest_query
        "SELECT DISTINCT pc.cod_pessoa, p.nome FROM dbo.Pessoa_Certificado pc INNER JOIN dbo.pessoa p ON pc.cod_pessoa = p.cod_pessoa WHERE p.nome LIKE ? OR pc.cod_pessoa LIKE ?",
        # 2. id_query (matricula)
        "SELECT pc.cod_pessoa, p.nome, pc.tipo_certificado, pc.cod_escola, pc.cod_curso, pc.cod_disciplina, d.nome AS nome_disciplina, pc.carga_horaria, pc.grade, pc.polo, FORMAT(pc.data_registro, 'dd/MM/yyyy') AS data_registro, pc.data_inicio, pc.data_conclusao, pc.data_emissao, pc.lote, pc.livro, pc.folha, pc.numero_registro, pc.cod_rastreamento, pc.retirado_por, pc.status, pc.observacao, pc.status_emissao, pc.data_solicitacao, pc.data_colacao_grau, pc.nota_tcc, pc.nota_01, pc.nota_02, pc.nota_03, pc.nota_04, pc.nota_05, pc.nota_06, pc.nota_07, pc.nota_08, pc.nota_09, pc.nota_10, pc.nota_11, pc.nota_12, pc.nota_13, pc.nota_14, pc.nota_15, pc.nota_16, pc.nota_17, pc.nota_18 FROM dbo.Pessoa_Certificado pc INNER JOIN dbo.pessoa p ON pc.cod_pessoa = p.cod_pessoa LEFT JOIN dbo.Disciplina d ON pc.cod_disciplina = d.cod_disciplina WHERE pc.cod_pessoa = ? ORDER BY pc.data_registro ASC",
        # 3. name_query (nome)
        "SELECT pc.cod_pessoa, p.nome, pc.tipo_certificado, pc.cod_escola, pc.cod_curso, pc.cod_disciplina, d.nome AS nome_disciplina, pc.carga_horaria, pc.grade, pc.polo, FORMAT(pc.data_registro, 'dd/MM/yyyy') AS data_registro, pc.data_inicio, pc.data_conclusao, pc.data_emissao, pc.lote, pc.livro, pc.folha, pc.numero_registro, pc.cod_rastreamento, pc.retirado_por, pc.status, pc.observacao, pc.status_emissao, pc.data_solicitacao, pc.data_colacao_grau, pc.nota_tcc, pc.nota_01, pc.nota_02, pc.nota_03, pc.nota_04, pc.nota_05, pc.nota_06, pc.nota_07, pc.nota_08, pc.nota_09, pc.nota_10, pc.nota_11, pc.nota_12, pc.nota_13, pc.nota_14, pc.nota_15, pc.nota_16, pc.nota_17, pc.nota_18 FROM dbo.Pessoa_Certificado pc INNER JOIN dbo.pessoa p ON pc.cod_pessoa = p.cod_pessoa LEFT JOIN dbo.Disciplina d ON pc.cod_disciplina = d.cod_disciplina WHERE p.nome LIKE ? ORDER BY pc.data_registro ASC",
        # 4. cpf_query (cpf)
        "SELECT pc.cod_pessoa, p.nome, pc.tipo_certificado, pc.cod_escola, pc.cod_curso, pc.cod_disciplina, d.nome AS nome_disciplina, pc.carga_horaria, pc.grade, pc.polo, FORMAT(pc.data_registro, 'dd/MM/yyyy') AS data_registro, pc.data_inicio, pc.data_conclusao, pc.data_emissao, pc.lote, pc.livro, pc.folha, pc.numero_registro, pc.cod_rastreamento, pc.retirado_por, pc.status, pc.observacao, pc.status_emissao, pc.data_solicitacao, pc.data_colacao_grau, pc.nota_tcc, pc.nota_01, pc.nota_02, pc.nota_03, pc.nota_04, pc.nota_05, pc.nota_06, pc.nota_07, pc.nota_08, pc.nota_09, pc.nota_10, pc.nota_11, pc.nota_12, pc.nota_13, pc.nota_14, pc.nota_15, pc.nota_16, pc.nota_17, pc.nota_18 FROM dbo.Pessoa_Certificado pc INNER JOIN dbo.pessoa p ON pc.cod_pessoa = p.cod_pessoa LEFT JOIN dbo.Disciplina d ON pc.cod_disciplina = d.cod_disciplina WHERE p.cpf_cnpj LIKE ? ORDER BY pc.data_registro ASC",
        # 5. columns
        ['Matricula', 'Nome', 'Tipo Certificado', 'Cod Escola', 'Cod Curso', 'Cod Disciplina', 'Nome Disciplina', 'Carga Horária', 'Grade', 'Polo', 'Data Registro', 'Data Início', 'Data Conclusão', 'Data Emissão', 'Lote', 'Livro', 'Folha', 'Número Registro', 'Cod Rastreamento', 'Retirado Por', 'Status', 'Observação', 'Status Emissao', 'Data Solicitação', 'Data Colacao Grau', 'Nota TCC', 'Nota 01', 'Nota 02', 'Nota 03', 'Nota 04', 'Nota 05', 'Nota 06', 'Nota 07', 'Nota 08', 'Nota 09', 'Nota 10', 'Nota 11', 'Nota 12', 'Nota 13', 'Nota 14', 'Nota 15', 'Nota 16', 'Nota 17', 'Nota 18']
    ),
    
    "Ocorrência": (
        # 1. suggest_query (nome, matricula) - 4 params
        """(SELECT DISTINCT o.matricula_aluno, p.nome 
            FROM dbo.Ocorrencias o INNER JOIN dbo.pessoa p ON o.matricula_aluno = p.cod_pessoa 
            WHERE p.nome LIKE ? OR o.matricula_aluno LIKE ?)
           UNION
           (SELECT DISTINCT matricula_aluno, nome_aluno AS nome 
            FROM dbo.ocorrencias_novo 
            WHERE nome_aluno LIKE ? OR matricula_aluno LIKE ?)""", 
        
        # 2. id_query (matricula) - 2 params
        """SELECT T.matricula_aluno, T.nome, T.tipo, T.data, T.hora, T.descricao, T.usuario, T.tipo_observacao, T.data_observacao, T.descricao_observacao, T.hora_observacao 
           FROM (
               SELECT 
                   o.matricula_aluno, p.nome, o.tipo, FORMAT(o.data, 'dd/MM/yyyy') as data, o.hora, o.descricao, o.usuario, 
                   CASE WHEN po.tipo_observacao = 'F' THEN 'Financeiro' WHEN po.tipo_observacao = 'A' THEN 'Acadêmico' ELSE po.tipo_observacao END AS tipo_observacao, 
                   FORMAT(po.data_observacao, 'dd/MM/yyyy') as data_observacao, po.descricao AS descricao_observacao, po.hora AS hora_observacao,
                   ISNULL(po.data_observacao, o.data) AS sort_date
               FROM dbo.Ocorrencias o 
               LEFT JOIN dbo.PessoaObservacao po ON o.matricula_aluno = po.cod_pessoa 
               INNER JOIN dbo.pessoa p ON o.matricula_aluno = p.cod_pessoa 
               WHERE o.matricula_aluno = ? 
               UNION ALL
               SELECT
                   matricula_aluno, nome_aluno AS nome, tipo, FORMAT(data, 'dd/MM/yyyy') as data,
                   FORMAT(data, 'HH:mm:ss') as hora, descricao_novo AS descricao, usuario,
                   'Nova Ocorrência' AS tipo_observacao, NULL AS data_observacao,
                   NULL AS descricao_observacao, NULL AS hora_observacao,
                   data AS sort_date
               FROM dbo.ocorrencias_novo
               WHERE matricula_aluno = ?
           ) AS T
           ORDER BY T.sort_date DESC""", 
        
        # 3. name_query (nome) - 2 params
        """SELECT T.matricula_aluno, T.nome, T.tipo, T.data, T.hora, T.descricao, T.usuario, T.tipo_observacao, T.data_observacao, T.descricao_observacao, T.hora_observacao 
           FROM (
               SELECT 
                   o.matricula_aluno, p.nome, o.tipo, FORMAT(o.data, 'dd/MM/yyyy') as data, o.hora, o.descricao, o.usuario, 
                   CASE WHEN po.tipo_observacao = 'F' THEN 'Financeiro' WHEN po.tipo_observacao = 'A' THEN 'Acadêmico' ELSE po.tipo_observacao END AS tipo_observacao, 
                   FORMAT(po.data_observacao, 'dd/MM/yyyy') as data_observacao, po.descricao AS descricao_observacao, po.hora AS hora_observacao,
                   ISNULL(po.data_observacao, o.data) AS sort_date
               FROM dbo.Ocorrencias o 
               LEFT JOIN dbo.PessoaObservacao po ON o.matricula_aluno = po.cod_pessoa 
               INNER JOIN dbo.pessoa p ON o.matricula_aluno = p.cod_pessoa 
               WHERE p.nome LIKE ?
               UNION ALL
               SELECT
                   matricula_aluno, nome_aluno AS nome, tipo, FORMAT(data, 'dd/MM/yyyy') as data,
                   FORMAT(data, 'HH:mm:ss') as hora, descricao_novo AS descricao, usuario,
                   'Nova Ocorrência' AS tipo_observacao, NULL AS data_observacao,
                   NULL AS descricao_observacao, NULL AS hora_observacao,
                   data AS sort_date
               FROM dbo.ocorrencias_novo
               WHERE nome_aluno LIKE ?
           ) AS T
           ORDER BY T.sort_date DESC""", 
           
        # 4. cpf_query (cpf) - 2 params
        """SELECT T.matricula_aluno, T.nome, T.tipo, T.data, T.hora, T.descricao, T.usuario, T.tipo_observacao, T.data_observacao, T.descricao_observacao, T.hora_observacao 
           FROM (
               SELECT 
                   o.matricula_aluno, p.nome, o.tipo, FORMAT(o.data, 'dd/MM/yyyy') as data, o.hora, o.descricao, o.usuario, 
                   CASE WHEN po.tipo_observacao = 'F' THEN 'Financeiro' WHEN po.tipo_observacao = 'A' THEN 'Acadêmico' ELSE po.tipo_observacao END AS tipo_observacao, 
                   FORMAT(po.data_observacao, 'dd/MM/yyyy') as data_observacao, po.descricao AS descricao_observacao, po.hora AS hora_observacao,
                   ISNULL(po.data_observacao, o.data) AS sort_date
               FROM dbo.Ocorrencias o 
               LEFT JOIN dbo.PessoaObservacao po ON o.matricula_aluno = po.cod_pessoa 
               INNER JOIN dbo.pessoa p ON o.matricula_aluno = p.cod_pessoa 
               WHERE p.cpf_cnpj LIKE ?
               UNION ALL
               SELECT
                   matricula_aluno, nome_aluno AS nome, tipo, FORMAT(data, 'dd/MM/yyyy') as data,
                   FORMAT(data, 'HH:mm:ss') as hora, descricao_novo AS descricao, usuario,
                   'Nova Ocorrência' AS tipo_observacao, NULL AS data_observacao,
                   NULL AS descricao_observacao, NULL AS hora_observacao,
                   data AS sort_date
               FROM dbo.ocorrencias_novo
               WHERE matricula_aluno IN (SELECT cod_pessoa FROM dbo.pessoa WHERE cpf_cnpj LIKE ?)
           ) AS T
           ORDER BY T.sort_date DESC""", 
        
        # 5. columns
        ['Matricula', 'Nome', 'Tipo', 'Data', 'Hora', 'Descrição', 'Usuário', 'Tipo Observação', 'Data Observação', 'Descrição Observação', 'Hora Observação']
    ),

    "Nota/Falta": (
        # 1. suggest_query
        "SELECT DISTINCT nf.matricula_aluno, p.nome FROM dbo.NotaFalta nf INNER JOIN dbo.pessoa p ON nf.matricula_aluno = p.cod_pessoa WHERE p.nome LIKE ? OR nf.matricula_aluno LIKE ?",
        # 2. id_query (matricula)
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
        # 3. name_query (nome)
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
        # 4. cpf_query (cpf)
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
            WHERE p.cpf_cnpj LIKE ?
            ORDER BY c.nome""",
        # 5. columns
        ['Matricula', 'Nome', 'Média Final', 'Nome Disciplina', 'Cod Turma', 'Cod Curso', 'Nome Curso', 'Cod Disciplina', 'Situação', 'Carga Horária', 'Descrição Atividade Extra', 'Data Atividade Extra', 'Carga Horária Extra', 'Tipo Atividade Extra']
    ),
    "Requerimento": (
        # 1. suggest_query
        "SELECT DISTINCT pr.cod_pessoa, p.nome FROM LogGeo.Pessoa_Requerimento pr INNER JOIN dbo.pessoa p ON pr.cod_pessoa = p.cod_pessoa WHERE p.nome LIKE ? OR pr.cod_pessoa LIKE ?",
        # 2. id_query (matricula)
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
        # 3. name_query (nome)
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
        # 4. cpf_query (cpf)
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
        "WHERE p.cpf_cnpj LIKE ? "
        "ORDER BY c.nome",
        # 5. columns
        ['Matricula', 'Nome', 'Cod Requerimento', 'Descrição Requerimento', 'Número Protocolo', 'Data Requerimento', 'Status', 'Usuário', 'Chave', 'Cod Turma', 'Cod Curso', 'Nome Curso', 'Data Previsão Entrega', 'Departamento Principal', 'Tipo Log', 'Data Hora Log', 'Usuário Log', 'Data Detalhe', 'Usuário Detalhe', 'Departamento Detalhe', 'Descrição Detalhe', 'Status Detalhe', 'Data Hora Log Detalhe', 'Usuário Log']
    ),
    "Matrícula": (
        # 1. suggest_query
        "SELECT DISTINCT m.matricula_aluno, p.nome AS nome_aluno FROM dbo.matricula m JOIN dbo.pessoa p ON m.matricula_aluno = p.cod_pessoa WHERE p.nome LIKE ? OR m.matricula_aluno LIKE ?",
        # 2. id_query (matricula)
        "SELECT m.matricula_aluno, p.nome AS nome_aluno, m.cod_turma, t.cod_curso, c.nome AS nome_curso, m.situacao, em.desc_situacao, m.resultado_final, "
        "CASE WHEN m.resultado_final = 'T' THEN 'Trancado' WHEN m.resultado_final = 'AC' THEN 'Aulas Concluídas' WHEN m.resultado_final = 'A' THEN 'Aprovado' WHEN m.resultado_final = 'S' THEN 'Cancelado' WHEN m.resultado_final = 'AG' THEN 'Aguardando' WHEN m.resultado_final = 'TE' THEN 'Turma Encerrada' WHEN m.resultado_final = 'D' THEN 'Desistente' WHEN m.resultado_final = 'G' THEN 'Aguardando Solicitação' WHEN m.resultado_final = 'R' THEN 'Recuperação' when m.resultado_final = 'C' THEN 'Cursando' when m.resultado_final = 'M' THEN 'Matriculado' when m.resultado_final = 'B' THEN 'Bloq. DP’s' ELSE m.resultado_final END AS desc_resultado_final, m.data_matricula, m.data_situacao, m.situacao_complementar, m.representante, m.consultor, m.supervisor, m.data_cadastro, m.grade "
        "FROM dbo.matricula m "
        "JOIN dbo.pessoa p ON m.matricula_aluno = p.cod_pessoa "
        "JOIN dbo.turma t ON m.cod_turma = t.cod_turma "
        "JOIN dbo.curso c ON t.cod_curso = c.cod_curso "
        "LEFT JOIN (SELECT matricula_aluno, cod_turma, MAX(desc_situacao) AS desc_situacao FROM dbo.entity_Matricula GROUP BY matricula_aluno, cod_turma) em "
        "ON m.matricula_aluno = em.matricula_aluno AND m.cod_turma = em.cod_turma "
        "WHERE m.matricula_aluno = ? ",
        # 3. name_query (nome)
        "SELECT m.matricula_aluno, p.nome AS nome_aluno, m.cod_turma, t.cod_curso, c.nome AS nome_curso, m.situacao, em.desc_situacao, m.resultado_final, "
        "CASE WHEN m.resultado_final = 'T' THEN 'Trancado' WHEN m.resultado_final = 'AC' THEN 'Aulas Concluídas' WHEN m.resultado_final = 'A' THEN 'Aprovado' WHEN m.resultado_final = 'S' THEN 'Cancelado' WHEN m.resultado_final = 'AG' THEN 'Aguardando' WHEN m.resultado_final = 'TE' THEN 'Turma Encerrada' WHEN m.resultado_final = 'D' THEN 'Desistente' WHEN m.resultado_final = 'G' THEN 'Aguardando Solicitação' WHEN m.resultado_final = 'R' THEN 'Recuperação' when m.resultado_final = 'C' THEN 'Cursando' when m.resultado_final = 'M' THEN 'Matriculado' when m.resultado_final = 'B' THEN 'Bloq. DP’s' ELSE m.resultado_final END AS desc_resultado_final, m.data_matricula, m.data_situacao, m.situacao_complementar, m.representante, m.consultor, m.supervisor, m.data_cadastro, m.grade "
        "FROM dbo.matricula m "
        "JOIN dbo.pessoa p ON m.matricula_aluno = p.cod_pessoa "
        "JOIN dbo.turma t ON m.cod_turma = t.cod_turma "
        "JOIN dbo.curso c ON t.cod_curso = c.cod_curso "
        "LEFT JOIN (SELECT matricula_aluno, cod_turma, MAX(desc_situacao) AS desc_situacao FROM dbo.entity_Matricula GROUP BY matricula_aluno, cod_turma) em "
        "ON m.matricula_aluno = em.matricula_aluno AND m.cod_turma = em.cod_turma "
        "WHERE p.nome LIKE ?",
        # 4. cpf_query (cpf)
        "SELECT m.matricula_aluno, p.nome AS nome_aluno, m.cod_turma, t.cod_curso, c.nome AS nome_curso, m.situacao, em.desc_situacao, m.resultado_final, "
        "CASE WHEN m.resultado_final = 'T' THEN 'Trancado' WHEN m.resultado_final = 'AC' THEN 'Aulas Concluídas' WHEN m.resultado_final = 'A' THEN 'Aprovado' WHEN m.resultado_final = 'S' THEN 'Cancelado' WHEN m.resultado_final = 'AG' THEN 'Aguardando' WHEN m.resultado_final = 'TE' THEN 'Turma Encerrada' WHEN m.resultado_final = 'D' THEN 'Desistente' WHEN m.resultado_final = 'G' THEN 'Aguardando Solicitação' WHEN m.resultado_final = 'R' THEN 'Recuperação' when m.resultado_final = 'C' THEN 'Cursando' when m.resultado_final = 'M' THEN 'Matriculado' when m.resultado_final = 'B' THEN 'Bloq. DP’s' ELSE m.resultado_final END AS desc_resultado_final, m.data_matricula, m.data_situacao, m.situacao_complementar, m.representante, m.consultor, m.supervisor, m.data_cadastro, m.grade "
        "FROM dbo.matricula m "
        "JOIN dbo.pessoa p ON m.matricula_aluno = p.cod_pessoa "
        "JOIN dbo.turma t ON m.cod_turma = t.cod_turma "
        "JOIN dbo.curso c ON t.cod_curso = c.cod_curso "
        "LEFT JOIN (SELECT matricula_aluno, cod_turma, MAX(desc_situacao) AS desc_situacao FROM dbo.entity_Matricula GROUP BY matricula_aluno, cod_turma) em "
        "ON m.matricula_aluno = em.matricula_aluno AND m.cod_turma = em.cod_turma "
        "WHERE p.cpf_cnpj LIKE ?",
        # 5. columns
        ['Matricula', 'Nome', 'Cod Turma', 'Cod Curso', 'Nome Curso', 'Situação', 'Descrição Situação', 'Resultado Final', 'Descrição Resultado Final', 'Data Matrícula', 'Data Situação', 'Situação Complementar', 'Representante', 'Consultor', 'Supervisor', 'Data Cadastro', 'Grade']
    ),
    "Financeiro": (
            # 1. suggest_query
            "SELECT cod_pessoa, nome FROM dbo.pessoa WHERE nome LIKE ? OR cod_pessoa LIKE ?",
            # 2. id_query (matricula)
            "SELECT cb.cod_pessoa, p.nome AS nome_pessoa, cb.cod_servico, cb.parcela, cb.status, c.nome AS nome_curso, t.cod_curso, FORMAT(cb.data_vencimento, 'dd/MM/yyyy') AS data_vencimento, cb.valor_bruto, cb.valor_desconto, cb.valor_pago,  cb.cod_turma, cb.status_cobranca "
            "FROM dbo.cobranca cb "
            "JOIN dbo.Turma t ON cb.cod_turma = t.cod_turma "
            "JOIN dbo.Curso c ON t.cod_curso = c.cod_curso "
            "JOIN dbo.Pessoa p ON cb.cod_pessoa = p.cod_pessoa "
            "WHERE cb.cod_pessoa = ? "
            "ORDER BY t.cod_turma, "
            "CASE WHEN CHARINDEX('/', cb.parcela) > 0 THEN CAST(SUBSTRING(cb.parcela, 1, CHARINDEX('/', cb.parcela) - 1) AS INT) ELSE 0 END ASC, "
            "CASE cb.status WHEN 'PG' THEN 0 ELSE 1 END",
            # 3. name_query (nome)
            "SELECT cb.cod_pessoa, p.nome AS nome_pessoa, cb.cod_servico, cb.parcela, cb.status, c.nome AS nome_curso, t.cod_curso, FORMAT(cb.data_vencimento, 'dd/MM/yyyy') AS data_vencimento, cb.valor_bruto, cb.valor_desconto, cb.valor_pago,  cb.cod_turma, cb.status_cobranca "
            "FROM dbo.cobranca cb "
            "JOIN dbo.Turma t ON cb.cod_turma = t.cod_turma "
            "JOIN dbo.Curso c ON t.cod_curso = c.cod_curso "
            "JOIN dbo.Pessoa p ON cb.cod_pessoa = p.cod_pessoa "
            "WHERE p.nome LIKE ? "
            "ORDER BY t.cod_turma, "
            "CASE WHEN CHARINDEX('/', cb.parcela) > 0 THEN CAST(SUBSTRING(cb.parcela, 1, CHARINDEX('/', cb.parcela) - 1) AS INT) ELSE 0 END ASC, "
            "CASE cb.status WHEN 'PG' THEN 0 ELSE 1 END",
            # 4. cpf_query (cpf)
            "SELECT cb.cod_pessoa, p.nome AS nome_pessoa, cb.cod_servico, cb.parcela, cb.status, c.nome AS nome_curso, t.cod_curso, FORMAT(cb.data_vencimento, 'dd/MM/yyyy') AS data_vencimento, cb.valor_bruto, cb.valor_desconto, cb.valor_pago,  cb.cod_turma, cb.status_cobranca "
            "FROM dbo.cobranca cb "
            "JOIN dbo.Turma t ON cb.cod_turma = t.cod_turma "
            "JOIN dbo.Curso c ON t.cod_curso = c.cod_curso "
            "JOIN dbo.Pessoa p ON cb.cod_pessoa = p.cod_pessoa "
            "WHERE p.cpf_cnpj LIKE ? "
            "ORDER BY t.cod_turma, "
            "CASE WHEN CHARINDEX('/', cb.parcela) > 0 THEN CAST(SUBSTRING(cb.parcela, 1, CHARINDEX('/', cb.parcela) - 1) AS INT) ELSE 0 END ASC, "
            "CASE cb.status WHEN 'PG' THEN 0 ELSE 1 END",
            # 5. columns
            ['Matricula', 'Nome', 'Cod Serviço', 'Parcela', 'Status', 'Nome Curso', 'Cod Curso', 'Valor Desconto', 'Valor Pago', 'Cod Turma', 'Valor Bruto', 'Data Vencimento', 'Status Cobrança']
    ),
    "Relatórios": (
        "SELECT p.nome FROM dbo.pessoa WHERE 1=0",
        "SELECT p.nome FROM dbo.pessoa WHERE 1=0",
        "SELECT p.nome FROM dbo.pessoa WHERE 1=0",
        "SELECT p.nome FROM dbo.pessoa WHERE 1=0",
        ['Nome']
    ),
}

# --- Configuração do Flask e JWT ---
app = Flask(__name__)
CORS(app) 
app.config["JWT_SECRET_KEY"] = "SEU_SEGREDO_SUPER_SECRETO_MUDE_ISSO_AGORA"
jwt = JWTManager(app)
app.config["JWT_ALGORITHM"] = "HS256" # Adicione esta linha

# --- Decorador de permissão de Admin (REMOVIDO E SUBSTITUÍDO POR LÓGICA INTERNA) ---


# --- Endpoint de LOGIN (Sem alteração) ---
@app.route('/api/login', methods=['POST'])
def login():
    login = request.json.get('login', None)
    senha = request.json.get('senha', None)

    if not login or not senha:
        return jsonify({"error": "Login e senha são obrigatórios"}), 400

    query = "SELECT id, nome_colaborador, login, senha_hash, role, is_ativo FROM dbo.colaboradores WHERE login = ?"
    resultados = search_database(query, (login,))
    
    if not resultados:
        logging.warning(f"Tentativa de login falhou (Usuário não encontrado): {login}")
        return jsonify({"error": "Login ou senha inválidos"}), 401
    
    usuario = resultados[0]

    if not usuario['is_ativo']:
        logging.warning(f"Tentativa de login falhou (Usuário bloqueado): {login}")
        return jsonify({"error": "Este usuário está bloqueado"}), 403

    if not check_password_hash(usuario['senha_hash'], senha):
        logging.warning(f"Tentativa de login falhou (Senha incorreta): {login}")
        return jsonify({"error": "Login ou senha inválidos"}), 401

    additional_claims = {
        "role": usuario['role'],
        "nome": usuario['nome_colaborador']
    }
    access_token = create_access_token(identity=usuario['id'], additional_claims=additional_claims)
    
    logging.info(f"Login bem-sucedido para: {login}, Role: {usuario['role']}")
    
    return jsonify(
        access_token=access_token,
        user={
            "login": usuario['login'],
            "nome": usuario['nome_colaborador'],
            "role": usuario['role']
        }
    )


# --- Endpoint /api/search/all (PROTEGIDO) ---
@app.route('/api/search/all', methods=['GET'])
@jwt_required()
def search_all_sections():
    # ... (Seu código de busca, 100% sem alteração) ...
    query_param = request.args.get('q')
    is_cpf_search = request.args.get('cpf') == 'true'
    logging.info(f"[API GLOBAL] Recebida requisição, Query: {query_param}, BuscaCPF: {is_cpf_search}")
    if not query_param:
        return jsonify({"error": "Query de busca (q) é obrigatória"}), 400
    all_results = {}
    for section, (suggest_query, id_query, name_query, cpf_query, *_) in queries.items():
        if section == "Relatórios":
            all_results[section] = [] 
            continue
        try:
            logging.debug(f"[API GLOBAL] Buscando seção: {section}")
            if is_cpf_search:
                sql_query = cpf_query
                param_like = f'%{query_param}%'
                if section == "Ocorrência":
                    params = (param_like, param_like)
                else:
                    params = (param_like,)
            else:
                if query_param.isdigit():
                    sql_query = id_query
                    if section == "Ocorrência":
                        params = (query_param, query_param)
                    else:
                        params = (query_param,)
                else:
                    sql_query = name_query
                    param_like = f'%{query_param}%'
                    if section == "Ocorrência":
                         params = (param_like, param_like)
                    else:
                        params = (param_like,)
            results = search_database(sql_query, params)
            for row in results:
                for key, value in row.items():
                    if isinstance(value, (datetime, date)):
                        row[key] = value.isoformat()
            all_results[section] = results
            logging.debug(f"[API GLOBAL] Seção {section} retornou {len(results)} resultados.")
        except Exception as e:
            logging.error(f"[API GLOBAL] Erro ao processar seção {section}: {e}")
            all_results[section] = [] 
    logging.info(f"[API GLOBAL] Retornando resultados para {len(all_results)} seções.")
    return jsonify(all_results)

# --- Endpoint /api/ocorrencia/nova (PROTEGIDO E AUTOMATIZADO) ---
@app.route('/api/ocorrencia/nova', methods=['POST'])
@jwt_required()
def nova_ocorrencia():
    data = request.json
    claims = get_jwt()
    usuario_logado = claims.get('nome', 'Usuário Desconhecido')
    logging.info(f"[API INSERT] Recebida requisição do usuário logado: {usuario_logado}")

    try:
        matricula_aluno = data.get('matricula_aluno')
        nome_aluno = data.get('nome_aluno')
        descricao = data.get('descricao')
        data_hoje = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        tipo = 'A'
        
        if not matricula_aluno or not nome_aluno or not descricao:
            return jsonify({"success": False, "error": "Dados incompletos"}), 400

        query = """INSERT INTO dbo.ocorrencias_novo (matricula_aluno, nome_aluno, data, descricao_novo, tipo, usuario)
                   VALUES (?, ?, CONVERT(DATETIME, ?, 120), ?, ?, ?)"""
        params = (matricula_aluno, nome_aluno, data_hoje, descricao, tipo, usuario_logado)
        sucesso = execute_insert(query, params)

        if sucesso:
            return jsonify({"success": True, "message": "Ocorrência inserida com sucesso"})
        else:
            return jsonify({"success": False, "error": "Erro ao inserir no banco de dados"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --- ENDPOINTS DE RELATÓRIO (PROTEGIDOS COM ADMIN) ---
MASTER_COLUMN_LABELS = {
    'cod_pessoa': 'Matrícula', 'nome': 'Nome', 'Sexo': 'Sexo', 'endereco_residencial': 'Endereço',
    'bairro_residencial': 'Bairro', 'cidade_residencial': 'Cidade', 'estado_residencial': 'Estado',
    'cep_residencial': 'CEP', 'fone_residencial': 'Telefone Residencial', 'celular': 'Celular',
    'email': 'Email', 'rg': 'RG', 'cpf_cnpj': 'CPF/CNPJ', 'nascimento_data': 'Nascimento',
    'curso_nome': 'Curso', 'consultor': 'Consultor'
}
MASTER_COLUMN_MAP = {
    'cod_pessoa': 'p.cod_pessoa', 'nome': 'p.nome', 'Sexo': 'p.Sexo', 'endereco_residencial': 'p.endereco_residencial',
    'bairro_residencial': 'p.bairro_residencial', 'cidade_residencial': 'p.cidade_residencial', 'estado_residencial': 'p.estado_residencial',
    'cep_residencial': 'p.cep_residencial', 'fone_residencial': 'p.fone_residencial', 'celular': 'p.celular',
    'email': 'p.email', 'rg': 'p.rg', 'cpf_cnpj': 'p.cpf_cnpj', 'nascimento_data': 'p.nascimento_data',
    'curso_nome': 'c.nome', 'consultor': 'm.consultor'
}

@app.route('/api/report_filters/cursos', methods=['GET'])
@jwt_required()
def get_cursos():
    # --- MUDANÇA: Verificação de Admin INTERNA ---
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Acesso restrito a administradores"}), 403
    # --- FIM DA MUDANÇA ---
    
    try:
        query = "SELECT DISTINCT nome FROM dbo.curso WHERE nome IS NOT NULL AND nome <> '' ORDER BY nome"
        results = search_database(query, ())
        return jsonify([row['nome'] for row in results])
    except Exception as e:
        logging.error(f"[API Filtro Curso] Erro: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/report_filters/consultores', methods=['GET'])
@jwt_required()
def get_consultores():
    # --- MUDANÇA: Verificação de Admin INTERNA ---
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Acesso restrito a administradores"}), 403
    # --- FIM DA MUDANÇA ---

    try:
        query = "SELECT DISTINCT consultor FROM dbo.matricula WHERE consultor IS NOT NULL AND consultor <> '' ORDER BY consultor"
        results = search_database(query, ())
        return jsonify([row['consultor'] for row in results])
    except Exception as e:
        logging.error(f"[API Filtro Consultor] Erro: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/report_builder', methods=['GET'])
@jwt_required()
def report_builder():
    # --- MUDANÇA: Verificação de Admin INTERNA ---
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Acesso restrito a administradores"}), 403
    # --- FIM DA MUDANÇA ---
    
    try:
        # ... (Sua lógica de relatório, 100% sem alteração) ...
        requested_cols = request.args.get('cols', '').split(',')
        curso_filter = request.args.get('curso', 'Todos')
        consultor_filter = request.args.get('consultor', 'Todos')
        is_preview = request.args.get('preview') == 'true'
        is_export = request.args.get('export') == 'true'
        logging.debug(f"[API Relatório] Recebido. Cols: {requested_cols}, Curso: {curso_filter}, Consultor: {consultor_filter}")
        validated_cols = []
        for col in requested_cols:
            if col in MASTER_COLUMN_MAP:
                validated_cols.append(col)
        if not validated_cols:
            return jsonify({"error": "Nenhuma coluna válida selecionada"}), 400
        top_clause = "TOP 5" if is_preview else ""
        cols_sql = ", ".join([f"{MASTER_COLUMN_MAP[col]} AS {col}" for col in validated_cols])
        query = f"""
            SELECT DISTINCT {top_clause} {cols_sql} 
            FROM dbo.pessoa p
            LEFT JOIN dbo.matricula m ON p.cod_pessoa = m.matricula_aluno
            LEFT JOIN dbo.turma t ON m.cod_turma = t.cod_turma
            LEFT JOIN dbo.curso c ON t.cod_curso = c.cod_curso
        """
        where_clauses = []
        params = []
        if curso_filter and curso_filter != 'Todos':
            where_clauses.append("c.nome = ?")
            params.append(curso_filter)
        if consultor_filter and consultor_filter != 'Todos':
            where_clauses.append("m.consultor = ?")
            params.append(consultor_filter)
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        results = search_database(query, tuple(params)) 
        
        if is_export:
            logging.info(f"[API Relatório] Exportando {len(results)} linhas para CSV.")
            header_friendly = [MASTER_COLUMN_LABELS.get(col, col) for col in validated_cols]
            output = io.StringIO()
            output.write('\uFEFF') 
            writer = csv.writer(output, quoting=csv.QUOTE_ALL)
            writer.writerow(header_friendly)
            for row in results:
                processed_row = []
                for col in validated_cols:
                    value = row.get(col)
                    if isinstance(value, (datetime, date)):
                        processed_row.append(value.isoformat().split('T')[0])
                    else:
                        processed_row.append(value)
                writer.writerow(processed_row)
            output.seek(0)
            return Response(
                output,
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment;filename=relatorio_personalizado.csv"}
            )
        else:
            logging.info(f"[API Relatório] Retornando preview JSON com {len(results)} linhas.")
            for row in results:
                for key, value in row.items():
                    if isinstance(value, (datetime, date)):
                        row[key] = value.isoformat().split('T')[0]
            return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- NOVOS ENDPOINTS DE GERENCIAMENTO DE COLABORADORES (PROTEGIDOS COM ADMIN) ---

@app.route('/api/colaboradores', methods=['GET'])
@jwt_required()
def get_colaboradores():
    # --- MUDANÇA: Verificação de Admin INTERNA ---
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Acesso restrito a administradores"}), 403
    # --- FIM DA MUDANÇA ---

    try:
        query = "SELECT id, nome_colaborador, login, role, is_ativo FROM dbo.colaboradores ORDER BY nome_colaborador"
        results = search_database(query, ())
        return jsonify(results)
    except Exception as e:
        logging.error(f"[API Colaboradores] Erro ao listar: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/colaboradores', methods=['POST'])
@jwt_required()
def create_colaborador():
    # --- MUDANÇA: Verificação de Admin INTERNA ---
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Acesso restrito a administradores"}), 403
    # --- FIM DA MUDANÇA ---

    data = request.json
    nome = data.get('nome')
    login = data.get('login')
    senha = data.get('senha')
    role = data.get('role', 'User')

    if not nome or not login or not senha:
        return jsonify({"error": "Nome, login e senha são obrigatórios"}), 400
    
    if role not in ['User', 'Admin']:
        return jsonify({"error": "Role deve ser 'User' ou 'Admin'"}), 400

    try:
        senha_hash = generate_password_hash(senha, method="pbkdf2:sha256:600000")
        
        query = """
            INSERT INTO dbo.colaboradores (nome_colaborador, login, senha_hash, role, is_ativo)
            VALUES (?, ?, ?, ?, 1)
        """
        params = (nome, login, senha_hash, role)
        
        sucesso = execute_insert(query, params)
        
        if sucesso:
            return jsonify({"success": True, "message": "Colaborador criado com sucesso"}), 201
        else:
            return jsonify({"error": "Erro ao inserir no banco de dados, verifique se o login já existe"}), 500
    except Exception as e:
        logging.error(f"[API Colaboradores] Erro ao criar: {e}")
        if 'UNIQUE constraint' in str(e):
            return jsonify({"error": "Este login já está em uso"}), 409
        return jsonify({"error": str(e)}), 500

@app.route('/api/colaboradores/<int:id>', methods=['PUT'])
@jwt_required()
def update_colaborador(id):
    # --- MUDANÇA: Verificação de Admin INTERNA ---
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Acesso restrito a administradores"}), 403
    # --- FIM DA MUDANÇA ---

    data = request.json
    role = data.get('role')
    is_ativo = data.get('is_ativo')

    if role not in ['User', 'Admin']:
        return jsonify({"error": "Role inválida"}), 400
    if is_ativo not in [True, False, 1, 0]:
         return jsonify({"error": "Status 'is_ativo' inválido"}), 400

    current_user_id = get_jwt_identity()
    if id == current_user_id:
        logging.warning(f"Admin (ID: {current_user_id}) tentou modificar a si mesmo.")
        return jsonify({"error": "Um administrador não pode modificar o próprio acesso"}), 403

    try:
        query = "UPDATE dbo.colaboradores SET role = ?, is_ativo = ? WHERE id = ?"
        params = (role, is_ativo, id)
        
        sucesso = execute_insert(query, params)
        
        if sucesso:
            return jsonify({"success": True, "message": "Colaborador atualizado com sucesso"})
        else:
            return jsonify({"error": "Erro ao atualizar no banco de dados"}), 500
    except Exception as e:
        logging.error(f"[API Colaboradores] Erro ao atualizar: {e}")
        return jsonify({"error": str(e)}), 500
# --- FIM DAS MUDANÇAS ---


if __name__ == '__main__':
    # Roda o servidor Flask na porta 5000
    app.run(debug=True, port=5000)