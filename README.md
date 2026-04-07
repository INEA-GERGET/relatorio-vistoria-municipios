# Gerar e enviar laudos de vistoria - De Olho No Verde

## Sumário
1. [Descrição](#Descrição)
2. [Uso](#Uso)
   - [Sobre os arquivos](#Sobre-os-arquivos)
4. [Instalação](#Instalação)


## Descrição
Este repositório contém todos os arquivos necessárrios para gerar Relatórios Laudo do Alerta e Laudo de Emabrgo de forma automática.

## Uso
Esse script possui uma interface interativa no terminal, onde o usuário pode escolher qual tipo de laudo quer gerar, se vai gerar ou não a tabela de merge e selecionar os IDs dos alertas a serem processados.
O primeiro passo ao executar o [main.py](main.py) deverá ser essa tela:
```
==============================================================================================================
====================                       📃 GERÇÃO DE VISTORIAS 📃                      ====================
==============================================================================================================
Esteja conectado à internet e com a tabela 'df_id_vstr.xlsx' atualizada na pasta 'arquivos_fixos'!
==============================================================================================================

Deseja baixar os dados e gerar os relatórios agora? (s/n): 
```

Independente da sua decisão sobre a geração dos relatórios de vistoria, a próxima tela mostrar a opção para enviar os relatórios para os fiscais. 

```
==============================================================================================================
====================                         📧 ENVIO DE EMAILS 📧                        ====================
==============================================================================================================

Deseja iniciar o envio dos e-mails agora? (s/n):
```
### Sobre os arquivos 
Baixe todos os arquivos e pastas e salve em um único diretório. 

Sobre os arquivos:
1. **input**: Nesta pasta todos os arquivos iniciais do programa estarão aqui e serão baixados automaticamente. Nela deverão conter os seguintes arquivos:
   1. **assinaturas**: arquivos de fotos das assianturas dos fiscais.
   2. **autorizacao**: arquivos de anexo dos laudos.
   3. **CSVs**: Esta pasta deverá armazenar todas as tabelas provenientes do formulário. 
   4. **Pontos**: Aqui estarão mapas do local marcado no GPS.
   5. **RL**: Nesta pasta vão estár o relatório fotográfico a ser inserido no relatório.
2. **output**: Nesta pasta estarão os resultados do script: os relatórios de vistoria e os mapas.
3. **arquivos_fixos**: Nesta pasta estão os arquivos de imagem necessários para o layout do documento, tais como: papel timbrado, logos, cabeçalho, rodapé e referências.
   1. **df_id_vstr.xlsx**: Arquivo excel com o ID de Laudo de Vistoria.
4. **config**: Nesta pasta está o acesso para o Portal GEOINEA.
5. **logs**: Pasta com o aquivo de execução.
    
* [**main.py**](main.py): É o script principal, baixa os dados, gera os relatórios de vistoria e envia-os por email. 

## Instalação

Para utilizar os scripts é necessária a instalação das bibliotecas Python:

* **configparser**: Para ler arquivos de configuração.
* **os**: Para interagir com o sistema operacional, como manipular caminhos de arquivos.
* **logging**: Para registrar eventos e mensagens do sistema.
* **arcgis**: Para interagir com o ArcGIS.
* **pandas**: Para manipulação e análise de dados tabulares.
* **geopandas**: Para trabalhar com dados geoespaciais (camadas de feições).
* **matplotlib.pyplot**: Para criar gráficos e visualizações.
* **contextily**: Para adicionar mapas base (mapas de fundo) a gráficos criados com Matplotlib.
* **PIL (Pillow)**: Para manipulação de imagens. A biblioteca é importada como `Image` e `ImageDraw`.
* **reportlab**: Para gerar documentos PDF de forma programática.
* **warnings**: Para controlar avisos (warnings).
* **arcpy**: Para a automação de tarefas do ArcGIS Pro e ArcMap.
