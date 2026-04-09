# Gerar e enviar laudos de vistoria - De Olho No Verde

## Sumário
1. [Descrição](#Descrição)
2. [Uso](#Uso)
   - [Sobre os arquivos](#Sobre-os-arquivos)
4. [Instalação](#Instalação)


## Descrição
Este repositório contém todos os arquivos necessárrios para gerar Relatórios Laudo do Alerta e Laudo de Emabrgo de forma automática.

## Uso
Esse script possui uma interface interativa no terminal, onde o usuário pode escolher se vai gerar ou não os relatórios de vistoria.
O primeiro passo ao executar o [main.py](main.py) deverá ser essa tela:
```
==============================================================================================================
====================                       📃 GERÇÃO DE VISTORIAS 📃                      ====================
==============================================================================================================
Esteja conectado à internet e ao COGET!
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

Ao rodar o `main.py` surgirá uma pasta de inputs e uma de outputs. Os relatórios finais estarão em `output/relatorios`.

Sobre os arquivos:

1. **arquivos_fixos**: Nesta pasta estão os arquivos de imagem necessários para o layout do documento, tais como: papel timbrado, logos, cabeçalho, rodapé e referências.
   1.1. **df_id_vstr.xlsx**: Arquivo excel com o ID de Laudo de Vistoria.
2. **config**: Nesta pasta está o acesso para o Portal GEOINEA.
3. [**main.py**](main.py): É o script principal, baixa os dados, gera os relatórios de vistoria e envia-os por email. 
4. [**enviar_email.py**](enviar_email.py): É o código que envia os emails com o relatório anexado para os vistoriadores.
5. [**funcoes_script.py**](funcoes_script.py): É o códico com funções internas essenciais para o funcionamento do relatório, como baixar os inputs.  
4. [**id_relatorio.py**](id_relatorio.py): É o código que cria um ID único para cada relatório. O output dele fica armazenado no em `INPUT-SCRIPTS` no GOGET. 
5. [**layout_vistoria.py**](layout_vistoria.py): É o código responsável pela criação do relatório. 


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
