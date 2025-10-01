# netlify/functions/convert_file.py
import json
import base64
import pandas as pd # Necessário para ler CSV e JSONL
import io
import os

def handler(event, context):
    """
    Função handler para Netlify Functions.
    Recebe um arquivo codificado em base64, converte-o e retorna o arquivo convertido.
    """
    try:
        # Verifica se a requisição é um POST
        if event['httpMethod'] != 'POST':
            return {
                'statusCode': 405,
                'body': json.dumps({'message': 'Method Not Allowed'})
            }

        # Analisa o corpo da requisição (que vem em JSON)
        body = json.loads(event['body'])
        file_content_base64 = body.get('fileContent')
        filename = body.get('filename')

        if not file_content_base64 or not filename:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Conteúdo do arquivo ou nome do arquivo faltando.'})
            }

        # Decodifica o conteúdo do arquivo de base64 para bytes
        file_bytes = base64.b64decode(file_content_base64)
        file_stream = io.BytesIO(file_bytes)

        # Lógica de conversão baseada no seu script original
        converted_filename = ""
        converted_file_bytes = None
        content_type = ""

        if filename.endswith(".jsonl"):
            # JSONL → CSV
            df = pd.read_json(file_stream, lines=True)
            converted_filename = filename.replace(".jsonl", ".csv")
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            converted_file_bytes = csv_buffer.getvalue().encode('utf-8') # Converte a string para bytes UTF-8
            content_type = 'text/csv'

        elif filename.endswith(".csv"):
            # CSV → JSONL
            df = pd.read_csv(file_stream)
            converted_filename = filename.replace(".csv", ".jsonl")
            jsonl_buffer = io.StringIO()
            df.to_json(jsonl_buffer, orient="records", lines=True, force_ascii=False)
            converted_file_bytes = jsonl_buffer.getvalue().encode('utf-8') # Converte a string para bytes UTF-8
            content_type = 'application/jsonl' # Content type para JSONL é geralmente application/json ou text/plain, mas application/jsonl é mais específico

        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Formato de arquivo não suportado. Envie arquivos .csv ou .jsonl.'})
            }

        if converted_file_bytes is None:
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Erro interno na conversão. O arquivo pode estar vazio ou corrompido.'})
            }

        # Retorna o arquivo convertido, codificado novamente em base64
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': content_type,
                'Content-Disposition': f'attachment; filename="{converted_filename}"', # Informa ao navegador o nome do arquivo
            },
            'body': base64.b64encode(converted_file_bytes).decode('utf-8'), # Conteúdo do arquivo convertido em base64
            'isBase64Encoded': True # Informa ao Netlify que o corpo está em base64
        }

    except Exception as e:
        print(f"Erro na função: {e}") # Log de erro no console do Netlify
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Erro interno do servidor durante a conversão: {str(e)}. Verifique o formato do seu arquivo.'})
        }