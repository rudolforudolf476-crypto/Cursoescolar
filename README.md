# Assistência visual para Windows — protótipo

Captura a imagem e procura pessoas com YOLO. Quando o ponto estimado da cabeça
fica a até 25 píxeis do centro, reduz os movimentos físicos do rato para 20%.
Não puxa a mira, não faz snap e não gera movimento se o rato estiver parado.
Fica ativo ao executar. **F7 encerra**. Só atua com RedM em primeiro plano.
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

`aimassist.log`, na pasta do programa, regista arranques, saída por F7,
interrupções e exceções Python. O launcher mostra o código de saída e ativa
o diagnóstico de falhas nativas na consola. Se parar sem carregar em F7,
envie as últimas linhas do registo e a mensagem/código da consola. Um processo
terminado pelo Windows ou um crash nativo pode não conseguir gravar o motivo.

## Perfil experimental inspirado em playertargetting.ymt

```powershell
.\iniciar.bat --profile ymt-normal --aim-point head --radius 35 --slowdown 0.20
```

O programa continua externo, por imagem, sem alterar ficheiros do jogo.
`classic` é o perfil predefinido e mantém a desaceleração imediata anterior.
Para esta atualização, copie também o novo `softlock.py` juntamente com
`aimassist.py`, `targeting.py` e `friction.py`.

O perfil normal do XML enviado contém `SoftLockTimeToAcquireTarget=0.25` e
`SoftLockTime=2.5`. Aqui esses números são interpretados experimentalmente
como segundos: 0,25 de deteção contínua antes de aplicar resistência e no máximo
2,5 de assistência antes de voltar a adquirir. Não há documentação do motor
neste ficheiro que confirme equivalência com o comportamento interno do jogo.
A resistência continua fixa, sem snap, sem correções automáticas e sem seguimento
ativo da cabeça. Os valores não resolvem falhas da deteção visual.

Perder a deteção, sair do raio ou perder o foco liberta o rato imediatamente.
Saltos superiores a 75% do raio (mínimo 10 píxeis) e intervalos entre deteções
superiores a 0,30 segundos reiniciam a aquisição. Esses dois limites são escolhas
do protótipo, não valores retirados do YMT. Numa máquina lenta, o perfil pode
não chegar a ativar. A associação usa proximidade entre pontos, não identifica
pessoas: dois alvos próximos podem ser confundidos.

Não foram convertidos `SoftLockBreakValue=0.156`, distâncias, ângulos ou parâmetros
de stick: não existe uma escala demonstrada que os relacione com píxeis e rato.
Os tempos de blend também não foram aplicados para preservar a resistência fixa
pedida. F7 encerra. O perfil precisa de validação no Windows/RedM.

Para comparar com a versão anterior:

```powershell
.\iniciar.bat --profile classic --aim-point head --radius 35 --slowdown 0.20
```

## Diagnosticar pessoas não reconhecidas

```powershell
.\iniciar.bat --observe --profile classic --radius 15 --confidence 0.25 --imgsz 960
```

O modo de observação não altera o rato. Mostra todas as pessoas reconhecidas
na captura central, mesmo fora do raio: caixas e cabeça estimada em azul,
exclusões da heurística do próprio personagem em vermelho, referência central
em amarelo e alvo elegível em verde. Os números nas caixas são a confiança.
A consola distingue agora quantidade de pessoas reconhecidas de alvo no raio,
e informa a duração da inferência. Zero pessoas significa que o modelo não
reconheceu pessoas acima do limiar na captura; pessoas sem alvo no centro
significa que nenhuma referência passou os filtros de seleção.

`--imgsz 960` aumenta a resolução de inferência, não a resolução da captura
central de 640x640 (por predefinição). Pode ajudar o modelo mas não recupera
pormenores inexistentes e aumenta o custo. Compare com `--imgsz 640`.
Como alternativa, `--model yolov8s.pt` usa outro modelo COCO maior, transferido
no primeiro arranque. Não foi validado para RedM e pode ser demasiado lento em
CPU. Diminuir confiança pode aumentar falsos positivos. Não aumente a força
para tentar corrigir uma deteção ausente. Envie uma captura da janela de
observação para avaliar o alinhamento da cabeça estimada.
