import time
import matplotlib.pyplot as plt
#Ce code est juste un test pour voir les effets des différents coefficients PID mais il n'est pas utilisé dans le programme
def pid_controller(setpoint, pv, kp, ki, kd, previous_error, integral, dt):
    error = setpoint - pv
    integral += error * dt
    derivative = (error - previous_error) / dt
    control = kp * error + ki * integral + kd * derivative
    return control, error, integral

def main():
    setpoint = 5  # Valeur cible
    pv = 0.373  # Variable de processus initiale
    kp = 5  # Gain proportionnel
    ki = 10  # Gain intégral
    kd = 0.01  # Gain dérivé
    previous_error = 0
    integral = 0
    dt = 0.1  # Pas de temps

    time_steps = []
    pv_values = []
    control_values = []
    setpoint_values = []

    for i in range(100):  # Simulation sur 100 itérations
        control, error, integral = pid_controller(setpoint, pv, kp, ki, kd, previous_error, integral, dt)
        pv += control * dt  # Mise à jour de la variable de processus
        previous_error = error
        time_steps.append(i * dt)
        pv_values.append(pv)
        control_values.append(control)
        setpoint_values.append(setpoint)
        time.sleep(dt)

    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    plt.plot(time_steps, pv_values, label='Variable de Processus (PV)')
    plt.plot(time_steps, setpoint_values, label='Valeur Cible', linestyle='--')
    plt.xlabel('Temps (s)')
    plt.ylabel('Valeur')
    plt.title('Variable de Processus vs. Valeur Cible')
    plt.legend()
    plt.subplot(2, 1, 2)
    plt.plot(time_steps, control_values, label='Sortie de Contrôle')
    plt.xlabel('Temps (s)')
    plt.ylabel('Sortie de Contrôle')
    plt.title('Sortie de Contrôle au fil du Temps')
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
