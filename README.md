# Assistência visual para Windows — protótipo

Captura a imagem e procura pessoas com YOLO. Quando o ponto estimado da cabeça
fica a até 25 píxeis do centro, reduz os movimentos físicos do rato para 20%.
Não puxa a mira, não faz snap e não gera movimento se o rato estiver parado.
Fica ativo ao executar. **F8 encerra**. Só atua com RedM em primeiro plano.
Usa apenas onde as regras do servidor permitam automação.

## Instalação no Windows 10/11

Instale Python 3.11 ou 3.12 de 64 bits. Abra PowerShell nesta pasta:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Execute `iniciar.bat`. No primeiro arranque, o Ultralytics transfere o modelo
`yolov8n.pt`; precisa de acesso à Internet. As dependências ainda não têm um
lockfile; a instalação pode resolver versões diferentes no futuro.

Use o jogo em janela sem bordas no monitor principal. O centro utilizado é o do
monitor, não o da janela. Para validar a deteção sem mover a mira:

```powershell
.\iniciar.bat --observe
```

Para executar com ajustes:

```powershell
.\iniciar.bat --radius 25 --slowdown 0.20 --monitor 1
```

`--window-title` permite adaptar o filtro ao título real da janela do jogo.
`--model caminho\modelo.pt` permite usar pesos COCO compatíveis já disponíveis.

## Limites e validação

É um protótipo. `--slowdown 0.20` aplica 20% do movimento; valores mais baixos
produzem maior resistência. `--radius` define a distância ao ponto estimado da cabeça.
`--aim-point head` (predefinido) usa 12% da altura da caixa da pessoa;
`--aim-point torso` usa 30%. Isto não é deteção anatómica da cabeça: chapéus,
posturas e oclusão podem deslocar a referência.
A desaceleração usa um hook do Windows e entrada sintética. Jogos que leem
Raw Input podem ignorar este mecanismo; nesse caso não haverá desaceleração.
Não foi validado no RedM e não contorna Raw Input, anti-cheat ou bloqueios.
Após uma deteção, a desaceleração expira em 150 ms se não for renovada.

O modelo genérico não foi treinado nem validado para RedM: alvos pequenos, cenas
escuras e oclusão podem causar falhas. Não distingue aliados, inimigos ou NPCs.
Exclui caixas grandes que chegam à base da captura para reduzir a seleção do
próprio personagem; essa heurística também pode excluir um alvo muito próximo. A captura fornecida
serviu apenas como referência visual, não como validação do modelo.

O modo `--observe` abre uma janela de diagnóstico. Ao focá-la, o filtro de janela
pausa a captura; volte ao jogo para retomar. Não use o programa com outras
janelas que incluam o texto do filtro no título.

Neste ambiente Linux só é possível validar a lógica independente do Windows:

```sh
python3 -m unittest discover -s tests -v
```

A captura, a inferência e o controlo de rato têm de ser validados no Windows.

Para resistência forte perto da cabeça, sem snap:

```powershell
.\iniciar.bat --aim-point head --radius 15 --slowdown 0.05
```

Atualize também `targeting.py` ao atualizar `aimassist.py`. A mira não acompanha
um alvo que se afaste: este modo só reduz o movimento manual perto da referência.

## Encerramento inesperado

`aimassist.log`, na pasta do programa, regista arranques, saída por F8,
interrupções e exceções Python. O launcher mostra o código de saída e ativa
o diagnóstico de falhas nativas na consola. Se parar sem carregar em F8,
envie as últimas linhas do registo e a mensagem/código da consola. Um processo
terminado pelo Windows ou um crash nativo pode não conseguir gravar o motivo.
