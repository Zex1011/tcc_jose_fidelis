# Plano inicial de validação

## Fase A — software sem hardware

Objetivo: validar contratos e fluxo.

Executar:

```bash
pytest -q
python -m followbot.main --config config.mock.toml --max-cycles 100
```

Critérios:

- sem exceções;
- comandos variam coerentemente com a bbox sintética;
- logs são produzidos;
- STOP é enviado no início e no final.

## Fase B — câmera isolada

Motores e ESP fora do teste.

Validar:

- câmera é detectada;
- `capture()` retorna imagens corretas;
- resolução configurada;
- orientação correta;
- comportamento sob iluminação real.

Registrar tempo de captura.

## Fase C — IA isolada

Usar câmera real, comunicação mock.

Configuração:

```text
camera = picamera2
detector = ultralytics
communication = mock
```

Medir por pelo menos algumas centenas de ciclos:

- média de inferência;
- mediana;
- p95;
- p99;
- média do ciclo total;
- RAM;
- CPU;
- temperatura.

Comparar ao menos algumas resoluções de inferência, por exemplo:

```text
256
320
416
```

A lista exata pode ser ajustada ao modelo.

Também testar:

- uma pessoa central;
- pessoa pequena ao fundo;
- pessoa perto;
- duas pessoas;
- cruzamento;
- oclusão curta;
- entrada/saída pelas bordas.

## Fase D — serial isolada

Não conectar os motores ainda.

ESP recebe comandos e apenas imprime/ACK.

Validar:

- porta correta;
- baud rate;
- reset ao abrir serial;
- ACK;
- timeout;
- retry;
- sequência;
- watchdog.

Teste obrigatório:

1. enviar comandos;
2. desconectar/parar processo Python;
3. confirmar que o watchdog manda o estado lógico para STOP.

## Fase E — motores elevados

Carrinho com rodas fora do chão.

Implementar `applyVelocityReference()` e conferir:

```text
v positivo -> ambas as rodas para frente
w positivo -> giro para esquerda na convenção escolhida
w negativo -> giro para direita
STOP -> saída motora zero
```

Validar saturação.

## Fase F — controle visual em baixa velocidade

Área vazia, velocidade máxima severamente reduzida e parada física disponível.

Testes separados:

### Angular

Desabilitar avanço:

```text
max_linear = 0
```

Mover a pessoa lateralmente e verificar se o carrinho tenta centralizá-la.

Ajustar:

```text
angular_sign
kp_angular
horizontal_deadband
max_angular
```

### Linear

Depois de validar angular, permitir avanço baixo.

Ajustar:

```text
desired_height_ratio
kp_linear
height_deadband
max_linear
```

## Fase G — integração

Avaliar cenários:

- pessoa parada;
- pessoa caminhando devagar;
- curva;
- aproximação;
- afastamento;
- perda do alvo;
- reaparecimento;
- outra pessoa entrando no quadro.

## Métricas úteis para o TCC

### Computacionais

```text
capture_ms
inference_ms
tracking_ms
control_ms
communication_ms
cycle_total_ms
RAM
CPU
temperatura
```

### Tracking

```text
erro horizontal normalizado
taxa de perda do alvo
taxa de troca incorreta de alvo
tempo de reaquisição
```

### Controle

```text
erro médio de centralização
erro médio de altura relativa da bbox
overshoot lateral
oscilações
tempo para centralizar
tempo para atingir distância visual desejada
```

### Segurança/comunicação

```text
latência de ACK
taxa de retries
taxa de falhas
tempo até STOP após perda de comunicação
tempo até STOP após perda do alvo
```

## Critério para abandonar o loop síncrono

Não migrar para threads apenas porque “pode ser mais rápido”.

Primeiro medir.

A arquitetura síncrona só precisa ser substituída se os resultados mostrarem que:

- câmera fica excessivamente ociosa;
- latência de inferência torna o controle inadequado;
- frequência do loop fica abaixo do necessário;
- comunicação bloqueante gera impacto significativo.

Nesse caso, as interfaces atuais ainda podem ser mantidas e o orquestrador pode evoluir separadamente.
