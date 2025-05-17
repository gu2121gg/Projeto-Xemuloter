# Game Launcher Premium

Este é um lançador de jogos personalizado construído com Python e Tkinter, projetado para fornecer uma interface amigável para baixar, instalar e executar seus jogos favoritos. Ele oferece suporte a navegação por teclado e joystick, gerenciamento de downloads e uma interface visualmente atraente.

## Funcionalidades

* **Interface Gráfica Intuitiva:** Utiliza Tkinter para criar uma interface gráfica elegante e fácil de usar, com menus animados e cards de jogos informativos.
* **Gerenciamento de Jogos:** Carrega informações dos jogos a partir de um arquivo JSON, permitindo fácil adição ou remoção de jogos.
* **Download Integrado:** Implementa funcionalidade de download diretamente no aplicativo, com barra de progresso e tratamento de erros.
* **Instalação e Execução:** Permite instalar jogos (baixando os arquivos) e executá-los diretamente do lançador, com múltiplas tentativas de execução para garantir compatibilidade.
* **Navegação por Controle/Teclado:** Suporta navegação completa usando joystick ou teclado, ideal para setups de sala de estar.
* **Gerenciamento de Áudio:** Reproduz efeitos sonoros para melhorar a experiência do usuário.
* **Verificação de Integridade:** Verifica a integridade dos arquivos baixados usando MD5 para garantir que não estejam corrompidos.
* **Execução como Administrador:** Solicita privilégios de administrador se necessário.
* **Design Customizável:** Usa um arquivo de configuração (`config.json`) para facilitar a personalização de cores, dimensões e outros aspectos visuais.

## Como Usar

1.  **Pré-requisitos:**
    * Python 3.x instalado
    * Bibliotecas: `tkinter`, `PIL (Pillow)`, `pygame`, `requests`
2.  **Instalação das Bibliotecas:**
    ```bash
    pip install tk pillow pygame requests
    ```
3.  **Execução:**
    ```bash
    python main.py
    ```

## Estrutura do Código

O código é organizado em classes para melhor modularidade:

* `Config`:  Contém configurações do aplicativo (dimensões, cores, caminhos, etc.).
* `Utils`:  Fornece funções utilitárias (verificar administrador, conversão de cores, cálculo de MD5).
* `AudioManager`:  Gerencia a reprodução de áudio.
* `GameManager`:  Lida com o carregamento de informações dos jogos e verificação de instalação.
* `GameLauncherUI`:  Implementa a interface gráfica e a lógica principal do lançador.

## Arquivos Importantes

* `main.py`:  O arquivo principal do programa.
* `config.json`:  Arquivo de configuração.
* `assets/games.json`:  Arquivo JSON contendo informações sobre os jogos.
* `assets/audio/`:  Diretório contendo os arquivos de áudio.
* `downloads/`:  Diretório onde os jogos são baixados.

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para enviar pull requests ou abrir issues para relatar bugs ou sugerir melhorias.

## Licença mit

