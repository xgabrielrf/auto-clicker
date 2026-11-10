# Auto Clicker

Auto-clicker para Windows feito em Python, com interface dark (cinza escuro com detalhes vermelhos) e um diferencial: o modo **Recording**, que reproduz uma sequência de **cliques em pontos da tela intercalados com teclas do teclado**.

## Requisitos e execução

- Windows 10/11
- Python 3.10+ (testado com 3.14)

```bash
pip install -r requirements.txt
python main.py
```

Dependências: [`customtkinter`](https://github.com/TomSchimansky/CustomTkinter) (interface) e [`pynput`](https://github.com/moses-palmer/pynput) (mouse, teclado e hotkey global).

## Visão geral da interface

A janela principal é compacta (300 px de largura), **abre sempre no centro da tela** e tem:

- **Menu superior** com `Options`, `Repeat` e `Recording`. Cada item abre **uma janela própria** ao lado da principal (clicar de novo apenas a traz para frente; fechar só esconde, nada se perde).
- **Botão grande "Press F8 to click"** (Settings). Clique nele para abrir a janela *Hotkey Setting* e trocar a tecla. Durante a execução o texto vira "Press F8 to stop".
- **Versão** (ex.: `v1.0.0`) em cinza discreto, no canto direito do menu superior.
- **Barra de status** no rodapé: `Idle`, `Running · N clicks` e mensagens de aviso/erro.

O clicker é iniciado e parado **pela hotkey** (padrão **F8**), que funciona globalmente, mesmo com o app em segundo plano.

## Funcionalidades

### Settings — Hotkey Setting

Abre ao clicar no botão principal. Pressione a tecla desejada: ela aparece na caixa grande. **Ok** aplica; **Cancel** (ou fechar/Esc) descarta. Enquanto a janela está aberta a hotkey atual fica suspensa, para não disparar o clicker.

> Evite `F10` e `Alt`: o Windows os usa para ativar o menu do sistema e a janela pode "travar" até você apertar Esc.

### Options (janela 380 px)

- **Mouse:** Left / Right / Middle
- **Click:** Single / Double
- **Freeze the pointer:** mantém o cursor preso no ponto onde o clicker começou (modo simples) ou no último ponto clicado (modo Recording). Se você mover o mouse durante a execução, o ponteiro volta ao ponto.

### Repeat (janela 420 px)

- **Repeat [N] times:** executa N vezes (mínimo 1). No modo Recording, N = número de ciclos completos da sequência.
- **Repeat until stopped:** repete até você apertar a hotkey.
- **Interval:** `hours / mins / secs / milliseconds`. É o tempo entre um clique e o próximo (no Recording, entre cada passo). Com 0 é usado um piso de 1 ms.

### Recording — multiple clicks (janela 480 px)

Marque **Record and replay multiple clicks** para usar a lista de passos em vez do clique simples na posição atual do mouse.

| Botão | O que faz |
|---|---|
| **Pick point** | A janela principal e a do Recording somem e uma camada translúcida cobre a tela (todos os monitores). Clique no ponto desejado: o passo é salvo com o **Mouse/Click** escolhidos em Options naquele momento. `Esc` ou botão direito cancelam. O clique é capturado pela camada e **não** chega ao app que está embaixo. |
| **Add Key** | Pressione uma tecla para adicioná-la à sequência (vira **Cancel** durante a captura). A tecla da hotkey não é aceita (conflito). |
| **Clear** | Remove todos os passos. |
| **✕** (em cada linha) | Remove só aquele passo. |
| **Save…** | Salva a sequência atual em um arquivo `.acseq`. **Sempre pergunta onde salvar.** |
| **Load…** | Carrega um arquivo `.acseq` (o seletor só mostra esse formato). **Substitui** a lista atual e marca o Recording como ativo. Arquivos inválidos são recusados com uma mensagem. |

Exemplo de lista:

```
1.  Left · Single @ (812, 440)
2.  Key: enter
3.  Right · Double @ (1200, 300)
```

Os passos são executados em ordem, com o **Interval** entre eles. Se o Recording estiver marcado e a lista vazia, o clicker avisa e não inicia.

## Persistência

### Estado automático

Tudo é gravado **em tempo real** no arquivo `auto-clicker-state.json`, na pasta em que o programa foi iniciado (raiz do projeto; ao lado do `.exe` se for empacotado), e restaurado ao abrir:

- hotkey, **Options** e **Repeat** (incluindo o Interval);
- **Recording**: checkbox e a lista de passos — a cada adicionar/remover/limpar/carregar.

O bloco `recording` só passa a ser gravado depois que o Recording foi selecionado pela primeira vez. Se o arquivo estiver corrompido, ele é renomeado para `auto-clicker-state.json.corrupt` e o app abre com os padrões. O arquivo está no `.gitignore`.

### Arquivos de sequência (`.acseq`)

Formato escolhido: **JSON com extensão própria `.acseq`** (texto legível e editável):

```json
{
  "format": "auto-clicker-sequence",
  "version": 1,
  "steps": [
    {"type": "click", "x": 812, "y": 440, "button": "Left", "double": false},
    {"type": "key", "key": "enter"}
  ]
}
```

## Estrutura do projeto

```
auto-clicker/
├─ main.py                     # ponto de entrada
├─ config.py                   # constantes, versão (APP_VERSION), larguras das janelas, padrões
├─ requirements.txt            # dependências de execução
├─ requirements-dev.txt        # + PyInstaller e Pillow (build do .exe)
├─ tools/build.py              # gera dist/Auto-Clicker-vX.Y.Z.exe
├─ README.md
├─ assets/icon_data.py         # ícone (PNG 128x128) em base64
├─ core/                       # lógica, sem dependência de UI
│  ├─ actions.py               # ClickAction / KeyAction (+ conversão para/de dict)
│  ├─ engine.py                # ClickEngine (thread): repeat, intervalo, freeze, recording
│  ├─ input_backend.py         # pynput: mover, clicar, pressionar tecla
│  ├─ hotkey.py                # hotkey global
│  ├─ capture.py               # captura de teclas (Add Key / Hotkey Setting)
│  ├─ keys.py                  # tecla pynput <-> nome ("f8", "enter")
│  └─ storage.py               # estado automático e arquivos .acseq
├─ ui/
│  ├─ app.py                   # janela principal e ligação UI <-> engine <-> estado
│  ├─ menubar.py               # menu superior
│  ├─ theme.py                 # paleta e fontes
│  ├─ widgets.py               # campos e botões estilizados
│  ├─ icon.py                  # ícone da janela/barra de tarefas
│  ├─ point_picker.py          # overlay do Pick point
│  └─ windows/                 # base, options, repeat, recording, hotkey
└─ tests/                      # test_engine.py, test_storage.py
```

## Testes

```bash
python -m unittest discover -s tests -t .
```

## Versão, executável e releases

A versão fica em **um único lugar**: `APP_VERSION` em [`config.py`](config.py) (formato `MAJOR.MINOR.PATCH`, ex.: `1.0.0`). Ela define o nome do executável, as propriedades do `.exe` e deve coincidir com a tag do git (`v1.0.0`).

### Gerar o executável

```bash
pip install -r requirements-dev.txt
python tools/build.py
```

Saída: `dist/Auto-Clicker-v1.0.0.exe` (o nome do arquivo usa hífen para não gerar problemas no GitHub Releases; arquivo único, sem console, com o ícone do app). `dist/` e `build/` estão no `.gitignore`: **o `.exe` não vai para o repositório**, e sim para o GitHub Releases.

O programa empacotado grava o `auto-clicker-state.json` na mesma pasta do `.exe`, então coloque-o numa pasta onde você tenha permissão de escrita.

### Publicar uma nova versão

1. Altere `APP_VERSION` em `config.py` (e atualize este README se algo mudou).
2. Gere o executável (`python tools/build.py`).
3. Crie a tag `vX.Y.Z` e envie ao GitHub.
4. No GitHub, crie o **Release** dessa tag e anexe o `.exe` (pela página do repositório → *Releases* → *Draft a new release*, ou pelo `gh release create`).

Regra de versão: `PATCH` para correções, `MINOR` para funcionalidades novas compatíveis, `MAJOR` para mudanças que quebram o uso (ex.: formato do `.acseq`).

> O Windows SmartScreen / antivírus podem alertar sobre o `.exe` por ele não ser assinado digitalmente e por usar captura global de teclado (pynput). Clique em *Mais informações → Executar assim mesmo*.

## Notas e limitações

- **Apps como administrador:** o Windows bloqueia entrada simulada para janelas elevadas. Para clicar nelas, execute o Auto Clicker como administrador.
- No modo simples o clique acontece onde o mouse estiver. Use a hotkey e posicione o mouse no alvo.
- **Add Key** aceita uma tecla por passo (sem combinações como Ctrl+C) e a tecla é pressionada e solta.
- Alterar as configurações durante a execução só tem efeito na próxima vez que iniciar.
