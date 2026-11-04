/*
  Exemplo de receptor do protocolo do FollowBot para ESP32/Arduino.

  Pi -> ESP: CMD,<seq>,<linear>,<angular>\n
  ESP -> Pi: ACK,<seq>\n

  IMPORTANTE:
  - applyVelocityReference() é propositalmente um placeholder de integração.
    O alvo atual é um carrinho diferencial com duas rodas motrizes + apoio,
    controlado inicialmente em malha aberta. Os motores/driver já pertencem ao
    carrinho e esta função deve ser ligada à interface de acionamento existente.
  - O watchdog deve ser calibrado para ser MAIOR que o pior tempo normal de um
    ciclo de visão do Raspberry, mas pequeno o suficiente para parar o robô se
    o Raspberry travar ou o cabo for desconectado.
*/

#include <Arduino.h>

static constexpr unsigned long BAUD_RATE = 115200;
static constexpr unsigned long COMMAND_TIMEOUT_MS = 2000; // PROVISÓRIO: medir e ajustar.
static constexpr size_t LINE_BUFFER_SIZE = 96;

char lineBuffer[LINE_BUFFER_SIZE];
size_t lineLength = 0;
unsigned long lastValidCommandMs = 0;
bool stoppedByWatchdog = true;

void applyVelocityReference(float linear, float angular) {
  // TODO: mapear as referências (v, w) para a interface de motores existente.
  // No MVP elas são referências abstratas/calibráveis em malha aberta.
  // Se futuramente forem adotadas unidades físicas, para robô diferencial:
  //   v_left  = v - w * wheel_base / 2
  //   v_right = v + w * wheel_base / 2
  (void)linear;
  (void)angular;
}

void emergencyStop() {
  applyVelocityReference(0.0f, 0.0f);
}

void handleLine(char* line) {
  unsigned long seq = 0;
  float linear = 0.0f;
  float angular = 0.0f;

  int parsed = sscanf(line, "CMD,%lu,%f,%f", &seq, &linear, &angular);
  if (parsed != 3) {
    Serial.println("ERR,0,BAD_FORMAT");
    return;
  }

  applyVelocityReference(linear, angular);
  lastValidCommandMs = millis();
  stoppedByWatchdog = false;

  Serial.print("ACK,");
  Serial.println(seq);
}

void setup() {
  Serial.begin(BAUD_RATE);
  emergencyStop();
  lastValidCommandMs = millis();
  Serial.println("READY");
}

void loop() {
  while (Serial.available() > 0) {
    char c = static_cast<char>(Serial.read());

    if (c == '\n') {
      lineBuffer[lineLength] = '\0';
      if (lineLength > 0) {
        handleLine(lineBuffer);
      }
      lineLength = 0;
    } else if (c != '\r') {
      if (lineLength < LINE_BUFFER_SIZE - 1) {
        lineBuffer[lineLength++] = c;
      } else {
        lineLength = 0;
        Serial.println("ERR,0,LINE_TOO_LONG");
      }
    }
  }

  if (!stoppedByWatchdog && (millis() - lastValidCommandMs > COMMAND_TIMEOUT_MS)) {
    emergencyStop();
    stoppedByWatchdog = true;
    Serial.println("WATCHDOG_STOP");
  }
}
