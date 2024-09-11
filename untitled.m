% Mecanismo de 4 barras 
% Análisis y Síntesis de Mecanismos

clear; 
% Leer datos del Excel
data = readtable('trabajo joaquin.xlsx');

% Definir longitudes de los eslabones desde el archivo Excel
L1 = data.L1(1);
L2 = data.L2(1);
L3 = data.L3(1);
L4 = data.L4(1);

% Número de pasos para la animación
num_steps = 100;
theta2_forward = linspace(0, 133*pi/180, num_steps); % De 0 a 133 grados
theta2_backward = linspace(133*pi/180, 0, num_steps); % De 133 a 0 grados

% Coordenadas del punto de bancada (fijo)
x0 = 0; y0 = 0;

% Inicializar variables para almacenar las coordenadas de los puntos de trayectoria
trayectoria_L2_L3_x = [];
trayectoria_L2_L3_y = [];
trayectoria_L3_L4_x = [];
trayectoria_L3_L4_y = [];

% Bucle de animación cíclica
while true
    clf; % Limpiar la figura actual
    
    % Primera subgráfica para la animación de los eslabones
    subplot(2, 1, 1);
    axis equal;
    axis([-10 35 -10 20]);
    grid on;
    hold on;

    % Definir las líneas del mecanismo
    link1 = line([0, L1], [0, 0], 'Color', 'r', 'LineWidth', 2);
    link2 = line([0, 0], [0, 0], 'Color', 'g', 'LineWidth', 2);
    link3 = line([0, 0], [0, 0], 'Color', 'b', 'LineWidth', 2);
    link4 = line([0, L1], [0, 0], 'Color', 'm', 'LineWidth', 2);

    % Segunda subgráfica para la relación theta4 - theta2
    subplot(2, 1, 2);
    axis([0, 135, 0, 180]); % Fijar los ejes
    xlabel('Ángulo de entrada \theta_2 (grados)');
    ylabel('Ángulo de salida \theta_4 (grados)');
    title('Relación entre \theta_2 y \theta_4');
    grid on;
    hold on;

    % Bucle para el movimiento cíclico
    for k = 1:2
        % Seleccionar el vector de theta2 adecuado
        if k == 1
            theta2_vector = theta2_forward;
        else
            theta2_vector = theta2_backward;
        end

        % Bucle para el movimiento hacia adelante y de regreso
        for i = 1:num_steps
            % Calcular el ángulo theta2
            theta2 = theta2_vector(i);

            % Calcular las coordenadas del extremo del eslabón 2
            x2_end = x0 + L2 * cos(theta2);
            y2_end = y0 + L2 * sin(theta2);

            % Calcular el ángulo entre el eslabón 2 y el eslabón 3
            BD = sqrt(L1^2 + L2^2 - 2*L1*L2*cos(theta2));
            gamma = acos((L3^2 + L4^2 - BD.^2) / (2*L3*L4));

            % Calcular el ángulo entre el eslabón 3 y el eslabón 4
            theta3 = 2*atan((-L2*sin(theta2) + L4*sin(gamma)) / (L1 + L3 - L2*cos(theta2) - L4*cos(gamma)));
            theta4 = 2*atan((L2*sin(theta2) - L3*sin(gamma)) / (L2*cos(theta2) + L4 - L1 - L3*cos(gamma)));

            % Convertir ángulos de radianes a grados
            theta2_deg(i) = rad2deg(theta2);
            theta4_deg(i) = rad2deg(theta4);

            % Guardar las coordenadas de los puntos de trayectoria entre L2 y L3
            trayectoria_L2_L3_x = [trayectoria_L2_L3_x x2_end];
            trayectoria_L2_L3_y = [trayectoria_L2_L3_y y2_end];

            % Guardar las coordenadas de los puntos de trayectoria entre L3 y L4
            trayectoria_L3_L4_x = [trayectoria_L3_L4_x x2_end + L3 * cos(theta3)];
            trayectoria_L3_L4_y = [trayectoria_L3_L4_y y2_end + L3 * sin(theta3)];
            
            % Actualizar las posiciones de las líneas en la primera subgráfica
            subplot(2, 1, 1);
            set(link1, 'XData', [0, L1], 'YData', [0, 0]);
            set(link2, 'XData', [0, x2_end], 'YData', [0, y2_end]);
            set(link3, 'XData', [x2_end, x2_end + L3 * cos(theta3)], 'YData', [y2_end, y2_end + L3 * sin(theta3)]);
            set(link4, 'XData', [x2_end + L3 * cos(theta3), L1], 'YData', [y2_end + L3 * sin(theta3), 0]);

            % Dibujar los puntos de trayectoria en la primera subgráfica
            scatter(trayectoria_L2_L3_x(1:end-1), trayectoria_L2_L3_y(1:end-1), 'k', 'filled');
            scatter(trayectoria_L3_L4_x(1:end-1), trayectoria_L3_L4_y(1:end-1), 'k', 'filled');
            scatter(trayectoria_L2_L3_x(end), trayectoria_L2_L3_y(end), 'r', 'filled');
            scatter(trayectoria_L3_L4_x(end), trayectoria_L3_L4_y(end), 'r', 'filled');

            % Actualizar la gráfica de la relación theta4 - theta2 en la segunda subgráfica
            subplot(2, 1, 2);
            scatter(theta2_deg(1:end-1), theta4_deg(1:end-1), 'k', 'filled'); % Plot puntos anteriores
            scatter(theta2_deg(i), theta4_deg(i), 'r', 'filled'); % Resaltar el último punto en rojo
            xlabel('Ángulo de entrada \theta_2 (grados)');
            ylabel('Ángulo de salida \theta_4 (grados)');
            title('Relación entre \theta_2 y \theta_4');
            grid on;
            drawnow;
            pause(0.02);
        end
    end 
end
