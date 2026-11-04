# Protocolo Serial MVP

## Objetivo

Protocolo simples, legível e fácil de depurar para o primeiro protótipo.

Ainda não existe CRC/checksum porque USB serial já fornece uma camada de transporte razoavelmente confiável e a prioridade atual é validar o pipeline. Caso o meio físico mude ou os testes revelem corrupção, um checksum pode ser acrescentado.

## Configuração inicial

```text
115200 baud
8 data bits
sem paridade
1 stop bit
```

Os detalhes 8N1 são o padrão utilizado pelo pySerial quando não alterados.

## Comando

```text
CMD,<seq>,<linear>,<angular>\n
```

Exemplo:

```text
CMD,152,0.25000,-0.42000
```

Campos:

```text
CMD       tipo da mensagem
152       número de sequência
0.25000   referência linear
-0.42000  referência angular
```

## Confirmação

```text
ACK,<seq>\n
```

Exemplo:

```text
ACK,152
```

O Raspberry só considera confirmado o ACK que contém a sequência do comando atual.

## Erro

Forma opcional:

```text
ERR,<seq>,<reason>\n
```

Exemplo:

```text
ERR,152,BAD_RANGE
```

O exemplo de ESP implementa erros simples de parsing.

## Startup

O ESP pode emitir:

```text
READY
```

O Raspberry atualmente ignora linhas que não sejam o ACK esperado ou um `ERR` da sequência atual.

Isso permite mensagens de diagnóstico do ESP sem quebrar o protocolo.

## Retry

Se o ACK não chegar no timeout:

```text
reenviar o MESMO comando com a MESMA sequência
```

Isso é importante: a retransmissão representa a mesma operação lógica.

## Idempotência

Aplicar duas vezes o mesmo `(v,w)` é aceitável para este protocolo, portanto a retransmissão é naturalmente idempotente.

Uma evolução futura poderia fazer o ESP guardar a última sequência e apenas reenviar o ACK de duplicatas.

## Watchdog

O ESP deve manter:

```text
lastValidCommandMs
```

Se nenhum comando válido chegar antes do timeout:

```text
v=0
w=0
```

O timeout final depende do benchmark do Raspberry.

## Decisão ainda pendente: unidades

O protocolo não muda se os números representarem:

```text
m/s e rad/s
```

ou

```text
comandos normalizados
```

Mas essa semântica precisa ser documentada e implementada de forma idêntica dos dois lados antes do teste físico.
