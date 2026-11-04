# Decisões pendentes, decisões fechadas e riscos técnicos

Esta lista foi atualizada após a revisão de instalação e após a consolidação das decisões de hardware já tomadas. Itens marcados como **RESOLVIDO** não devem voltar a ser tratados como incógnitas arquiteturais; podem continuar exigindo calibração ou integração.

## 1. Computador embarcado — RESOLVIDO

Hardware-alvo do MVP:

```text
Raspberry Pi Zero 2
```

A viabilidade do detector continua dependente de benchmark no equipamento real.

## 2. Sistema operacional e arquitetura — PENDENTE

Ainda definir no Raspberry:

- versão exata do Raspberry Pi OS;
- 32 ou 64 bits;
- versão efetiva do Python no dispositivo;
- compatibilidade das wheels/dependências da IA.

O projeto de software exige atualmente Python 3.11+.

## 3. Câmera — PENDENTE CRÍTICO

A câmera disponível possui a marcação `UC436`, mas ainda não está confirmado se esse é o modelo comercial/controlador.

Precisamos determinar:

- se é Raspberry Camera/libcamera ou USB/UVC;
- campo de visão;
- orientação/montagem;
- resolução útil;
- comportamento em iluminação real.

O backend atual `Picamera2Camera` só deve ser usado se o hardware for compatível. Se a UC436 for USB/UVC, implementar backend OpenCV/V4L2 mantendo a interface `Camera`.

## 4. Microcontrolador — RESOLVIDO

```text
ESP32
```

A conexão prevista é USB/Serial. Ainda verificar no hardware real se abrir a serial provoca reset e qual `startup_delay_s` é adequado.

## 5. Tipo de locomoção — RESOLVIDO

Carrinho com:

```text
duas rodas motrizes + um ponto/roda de apoio
```

A cinemática é compatível com acionamento diferencial.

## 6. Semântica de `v` e `w` — DECISÃO DE MVP

No MVP em malha aberta, tratar:

```text
v = referência linear abstrata/calibrável
w = referência angular abstrata/calibrável
```

Não assumir que os valores são m/s e rad/s medidos. O protocolo permite migrar para unidades físicas futuramente sem alteração estrutural.

## 7. Encoders — FORA DO REQUISITO ATUAL

O MVP será validado inicialmente em **malha aberta**. Encoders não são requisito atual.

Se futuramente forem adicionados, o ESP32 poderá fechar a malha de velocidade local sem alterar o pipeline visual do Raspberry.

## 8. Motores e driver — INTEGRAÇÃO PENDENTE, HARDWARE FORA DO ESCOPO

O carrinho já possui sistema de motores configurado e os detalhes elétricos/mecânicos não fazem parte do escopo desta implementação.

A pendência de software é integrar:

```cpp
applyVelocityReference(linear, angular)
```

com a interface de acionamento já existente no ESP32/carrinho e calibrar a resposta em malha aberta.

## 9. Viabilidade do YOLO no Raspberry real

Implementação atual:

```text
YOLO26n / NCNN / imgsz=320
```

Isso precisa ser validado em termos de:

- RAM máxima;
- tempo médio de inferência;
- p95/p99 de inferência;
- temperatura;
- estabilidade por execução longa;
- precisão em pessoas pequenas;
- impacto de `imgsz=256`, `320`, `416` etc.

Se o wrapper Python/Ultralytics consumir memória ou tempo demais, próxima alternativa arquitetural:

```text
manter Detector interface
substituir implementação por NCNN nativo em C++
```

## 10. Frequência mínima de controle — META INICIAL DEFINIDA

O loop não possui período fixo. A meta inicial é sustentar **aproximadamente 1 ciclo por segundo ou mais** no Raspberry Pi Zero 2.

Precisamos medir:

```text
Hz efetivo = 1 / cycle_time
```

Depois determinar experimentalmente se o carrinho responde de modo suave e seguro nessa frequência.

Se o tempo de inferência dominar e a frequência for insuficiente, aí sim considerar:

- resolução menor;
- modelo diferente;
- C++;
- pipeline assíncrono;
- acelerador externo;
- outra placa.

## 11. Watchdog do ESP

O exemplo usa 2000 ms apenas como placeholder.

Regra futura recomendada:

```text
watchdog > p99 do tempo normal de ciclo + margem
```

mas ainda curto o bastante para interromper movimento rapidamente numa falha.

## 12. Ganhos do controle

Todos estes valores são iniciais:

```text
desired_height_ratio
kp_linear
kp_angular
max_linear
max_angular
deadbands
turn slowdown
```

Precisam de calibração em ambiente controlado.

## 13. Relação bbox-distância

Usar altura da bbox é apenas uma aproximação.

Varia com:

- altura da pessoa;
- postura;
- inclinação da câmera;
- oclusão;
- crop do detector;
- FOV da lente.

Nesta fase o objetivo é manter **distância visual**, não medir metros.

## 14. Troca indevida de pessoa

O tracker por centro mais próximo falhará em cenários como:

- duas pessoas se cruzando;
- alvo temporariamente ocluído;
- movimentos rápidos;
- entrada de outra pessoa próxima.

A hipótese atual deve ser testada antes de adotar ByteTrack/BoT-SORT/re-identificação ou outro método mais complexo.

## 15. Estratégia de aquisição inicial

A configuração usa `first`, mas a ordem das detecções não deve ser tratada como semântica forte.

Alternativas já suportadas:

- maior bbox;
- maior confiança;
- mais central.

Para um produto final seria interessante uma seleção explícita do usuário ou identificação mais robusta.

## 16. Reaquisição

Hoje:

```text
alvo desaparece -> STOP
mantém bbox anterior por N frames
se reaparece perto -> reacquire
após N falhas -> esquece alvo
```

**Comportamento previsto confirmado em 26/10/2026; implementação pendente:** incluir busca por rotação lenta e limitada, orientada pela tendência horizontal das últimas detecções válidas. Se o tempo de busca expirar ou não houver direção confiável, solicitar STOP, continuar observando e permitir nova seleção, sem exigir reinício pelo usuário. O código atual descrito acima ainda não implementa essa busca.

O tempo máximo, a velocidade de giro e os critérios de perda, tendência e recuperação permanecem a definir na metodologia. A especificação e o diagrama estão no [guia de diagramas do RPi](../../Documentacao/diagramas/software_rpi/README.md).

## 17. Obstáculos — risco crítico

Seguir uma pessoa visualmente **não equivale a navegar com segurança**.

A câmera pode ordenar avanço mesmo havendo:

- parede baixa;
- cadeira;
- degrau;
- animal;
- objeto fora da região da pessoa.

Para testes reais no chão deve haver no mínimo uma estratégia independente de parada/colisão. Sensores de proximidade, bumper físico ou outro mecanismo devem ser considerados antes de velocidades relevantes.

## 18. Parada física

Considerar um botão físico ou chave de corte de motores durante desenvolvimento.

Software não deve ser a única forma de interromper o protótipo.

## 19. Bluetooth para logs

Primeiro decidir o receptor:

- Android;
- notebook Linux/Windows;
- outro dispositivo.

Depois escolher:

### BLE GATT

Bom para telemetria estruturada e compatibilidade moderna, mas exige serviço/característica e gerenciamento de conexão.

### RFCOMM / SPP

Mais parecido com uma serial de texto e simples de visualizar em terminais compatíveis, porém o suporte do cliente varia.

O Raspberry sem sufixo `W` não possui wireless onboard; Zero W/Zero 2 W possuem Bluetooth.

## 20. Política de logs e imagens

A versão atual registra metadados das detecções, **não salva os frames**.

Se futuramente imagens forem persistidas para análise, definir:

- consentimento;
- retenção;
- anonimização;
- armazenamento;
- descarte.

Isso é particularmente relevante para um trabalho acadêmico envolvendo imagens de pessoas.
