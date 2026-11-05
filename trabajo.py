<?php
session_start();

// --- LÓGICA DE SEGURIDAD ESTRICTA (Te saca si recargas la página) ---
if (!isset($_SESSION['logueado']) || $_SESSION['logueado'] !== true) {
    header("Location: login.php"); 
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    // Si trae el pase, lo dejamos pasar y le quitamos el pase
    if (isset($_SESSION['pase_unico'])) {
        unset($_SESSION['pase_unico']); 
    } else {
        // Si recarga la página o entra directo, lo sacamos por seguridad
        session_destroy();
        header("Location: login.php");
        exit;
    }
}
// -------------------------------------------------------------------

$cedula = $n1 = $n2 = $a1 = $a2 = $tel = $dir = "";
$mensaje = "";
$tipo_mensaje = "success";

if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_POST['accion'])) {
    $accion = $_POST['accion'];
    $datos = [
        'accion' => $accion, 'cedula' => $_POST['cedula'] ?? '', 'nombre1' => $_POST['nombre1'] ?? '',
        'nombre2' => $_POST['nombre2'] ?? '', 'apellido1' => $_POST['apellido1'] ?? '',
        'apellido2' => $_POST['apellido2'] ?? '', 'telefono' => $_POST['telefono'] ?? '', 'direccion' => $_POST['direccion'] ?? ''
    ];
    $url_api = 'https://otra-vez-o7oo.onrender.com/procesar'; 
    
    $ch = curl_init($url_api);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($datos));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_TIMEOUT, 60); 
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false); 
    $resultado = curl_exec($ch); 
    curl_close($ch);
    
    $respuesta_json = json_decode($resultado, true);
    
    if ($respuesta_json) {
        $mensaje = $respuesta_json['mensaje'];
        if (strpos($mensaje, 'Error') !== false || strpos($mensaje, 'Aviso') !== false) $tipo_mensaje = "error";
        if ($accion == 'consultar' && isset($respuesta_json['datos'])) {
            $d = $respuesta_json['datos'];
            $cedula = $d['cedula'] ?? ''; $n1 = $d['nombre1'] ?? ''; $n2 = $d['nombre2'] ?? '';
            $a1 = $d['apellido1'] ?? ''; $a2 = $d['apellido2'] ?? ''; $tel = $d['telefono'] ?? ''; $dir = $d['direccion'] ?? '';
        }
    }
}
?>

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel de Registro Seguro</title>
    <link href="https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-main: #8da191; --panel-bg: #f4f6f4; --border-color: #4a5e4b;
            --text-main: #2c3b2d; --btn-bg: #d1dcd0; --btn-hover: #b2c4b1; --accent: #5c785e;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Courier Prime', monospace; }
        body { 
            background-color: var(--bg-main);
            background-image: url('data:image/svg+xml;utf8,<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg"><filter id="noise"><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="4" stitchTiles="stitch"/></filter><rect width="100%" height="100%" filter="url(%23noise)" opacity="0.05"/></svg>');
            color: var(--text-main); display: flex; height: 100vh; overflow: hidden;
        }
        
        /* MENÚ LATERAL */
        .sidebar { width: 80px; background: var(--panel-bg); border-right: 2px solid var(--border-color); display: flex; flex-direction: column; align-items: center; padding: 20px 0; z-index: 10; }
        .sidebar .logo { width: 50px; height: 50px; background: var(--btn-bg); border: 2px solid var(--border-color); border-radius: 50%; margin-bottom: 40px; display: flex; justify-content: center; align-items: center; font-size: 24px; }
        .sidebar .icon { width: 50px; height: 50px; margin-bottom: 15px; background: transparent; border: 2px solid transparent; border-radius: 10px; display: flex; justify-content: center; align-items: center; font-size: 22px; cursor: pointer; transition: 0.2s; text-decoration: none; color: var(--text-main); }
        .sidebar .icon:hover { background: var(--btn-bg); border-color: var(--border-color); }
        .sidebar .icon.active { background: var(--btn-bg); border-color: var(--border-color); }

        /* CONTENIDO PRINCIPAL */
        .main-content { flex: 1; padding: 30px 40px; overflow-y: auto; display: flex; flex-direction: column; }
        .header { display: flex; justify-content: flex-end; align-items: center; gap: 15px; margin-bottom: 20px; }
        
        /* BOTÓN DE BLOQUEO */
        .lock-btn { background: #f2dede; color: #a94442; border: 2px solid #a94442; padding: 8px 15px; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 14px; transition: 0.2s; display: flex; align-items: center; gap: 5px; }
        .lock-btn:hover { background: #ebcccc; }

        /* VISTAS (Formulario vs Lista) */
        .vista { display: none; }
        .vista.activa { display: block; }

        /* FORMULARIO */
        .grid { display: grid; grid-template-columns: 1.5fr 1fr; gap: 30px; flex: 1; }
        .card { background: var(--panel-bg); border: 2px solid var(--border-color); border-radius: 12px; padding: 25px; box-shadow: 4px 4px 0px rgba(74, 94, 75, 0.2); }
        .card h2 { font-size: 16px; color: var(--text-main); margin-bottom: 20px; text-transform: uppercase; border-bottom: 2px dashed var(--border-color); padding-bottom: 10px; }
        
        .input-row { display: flex; gap: 15px; margin-bottom: 15px; }
        .input-group { flex: 1; }
        .input-group label { display: block; font-size: 13px; color: var(--text-main); margin-bottom: 5px; font-weight: bold;}
        .input-group input { width: 100%; padding: 10px 12px; border-radius: 6px; border: 1px solid var(--border-color); background: #ffffff; color: var(--text-main); outline: none; font-size: 14px; }
        
        .btn-group { display: flex; gap: 10px; margin-top: 25px; flex-wrap: wrap; }
        .btn { padding: 10px 15px; border-radius: 6px; border: 1px solid var(--border-color); background: var(--btn-bg); color: var(--text-main); font-weight: bold; cursor: pointer; transition: 0.2s; text-decoration: none; text-align: center; font-size: 13px; }
        .btn:hover { background: var(--btn-hover); }
        .btn-primary { background: var(--accent); color: white; }
        .btn-primary:hover { background: var(--border-color); }
        
        .upload-card { display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; border-style: dashed; }
        .upload-icon { font-size: 40px; margin-bottom: 15px; }
        .upload-card h3 { font-size: 15px; color: var(--text-main); margin-bottom: 10px;}
        .upload-card p { font-size: 13px; color: var(--text-main); margin-bottom: 20px; line-height: 1.5; }
        input[type="file"]::file-selector-button { padding: 8px 12px; border-radius: 4px; border: 1px solid var(--border-color); background: var(--btn-bg); color: var(--text-main); cursor: pointer; font-weight: bold; margin-right: 10px; transition: 0.2s; }

        /* TABLA DE USUARIOS */
        .table-container { width: 100%; overflow-x: auto; background: var(--panel-bg); border: 2px solid var(--border-color); border-radius: 12px; padding: 20px; box-shadow: 4px 4px 0px rgba(74, 94, 75, 0.2); }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px dashed var(--border-color); font-size: 14px; }
        th { background: var(--btn-bg); font-weight: bold; text-transform: uppercase; font-size: 12px; letter-spacing: 1px; border-bottom: 2px solid var(--border-color); }
        tr:hover { background: rgba(0,0,0,0.02); }

        /* ALERTAS */
        .alert { padding: 12px; border-radius: 6px; margin-bottom: 20px; font-size: 14px; font-weight: bold; border-left: 4px solid; }
        .alert-success { background: #dff0d8; color: #3c763d; border-color: #3c763d; }
        .alert-error { background: #f2dede; color: #a94442; border-color: #a94442; }

        /* OVERLAY DE BLOQUEO */
        #lock-screen {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(20, 30, 25, 0.85); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
            z-index: 9999; display: none; flex-direction: column; justify-content: center; align-items: center;
            color: white; text-align: center;
        }
        #lock-screen h1 { font-size: 50px; margin-bottom: 20px; text-shadow: 0 0 20px #ff4d4d; }
        #lock-screen p { font-size: 18px; margin-bottom: 30px; }
        .unlock-input { padding: 15px; border-radius: 8px; border: none; font-size: 16px; width: 300px; text-align: center; margin-bottom: 15px; }
        .unlock-btn { padding: 15px 30px; background: #a94442; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.3s; }
        .unlock-btn:hover { background: #d9534f; }
    </style>
</head>
<body>

<!-- CAPA DE BLOQUEO -->
<div id="lock-screen">
    <h1>🔒 SISTEMA BLOQUEADO</h1>
    <p>La pantalla ha sido congelada por seguridad.</p>
    <input type="password" id="unlock-pass" class="unlock-input" placeholder="Ingresa contraseña (1234)">
    <button class="unlock-btn" onclick="desbloquear()">DESBLOQUEAR</button>
</div>

<!-- MENÚ LATERAL -->
<div class="sidebar">
    <div class="logo">🐸</div>
    <div class="icon active" id="btn-form" onclick="mostrarFormulario()" title="Registro">🏠</div>
    <div class="icon" id="btn-lista" onclick="mostrarLista()" title="Lista de Usuarios">👤</div>
    <a href="exportar.php" class="icon" title="Descargar Excel">📄</a>
    <a href="agente.php" class="icon" title="Hablar con la IA">🤖</a>
    <a href="logout.php" class="icon" title="Cerrar Sesión Definitivo">🚪</a>
</div>

<!-- CONTENIDO PRINCIPAL -->
<div class="main-content">
    <div class="header">
        <button onclick="congelarPantalla()" class="lock-btn">🔒 BLOQUEAR PANTALLA</button>
    </div>

    <?php if($mensaje): ?>
        <div class="alert <?php echo ($tipo_mensaje == 'error') ? 'alert-error' : 'alert-success'; ?>">
            <?php echo htmlspecialchars($mensaje); ?>
        </div>
    <?php endif; ?>

    <!-- VISTA 1: FORMULARIO -->
    <div id="vista-formulario" class="vista activa">
        <div class="grid">
            <div class="card">
                <h2>> Datos del Registro</h2>
                <form method="POST">
                    <div class="input-row"><div class="input-group"><label>Cédula / ID</label><input type="text" name="cedula" value="<?php echo htmlspecialchars($cedula); ?>" required></div></div>
                    <div class="input-row">
                        <div class="input-group"><label>Primer Nombre</label><input type="text" name="nombre1" value="<?php echo htmlspecialchars($n1); ?>"></div>
                        <div class="input-group"><label>Segundo Nombre</label><input type="text" name="nombre2" value="<?php echo htmlspecialchars($n2); ?>"></div>
                    </div>
                    <div class="input-row">
                        <div class="input-group"><label>Primer Apellido</label><input type="text" name="apellido1" value="<?php echo htmlspecialchars($a1); ?>"></div>
                        <div class="input-group"><label>Segundo Apellido</label><input type="text" name="apellido2" value="<?php echo htmlspecialchars($a2); ?>"></div>
                    </div>
                    <div class="input-row">
                        <div class="input-group"><label>Teléfono</label><input type="text" name="telefono" value="<?php echo htmlspecialchars($tel); ?>"></div>
                        <div class="input-group"><label>Dirección</label><input type="text" name="direccion" value="<?php echo htmlspecialchars($dir); ?>"></div>
                    </div>
                    <div class="btn-group">
                        <button type="submit" name="accion" value="guardar" class="btn btn-primary">GUARDAR</button>
                        <button type="submit" name="accion" value="consultar" class="btn">CONSULTAR</button>
                        <button type="submit" name="accion" value="editar" class="btn">EDITAR</button>
                        <button type="submit" name="accion" value="eliminar" class="btn" style="color:#a94442; border-color:#a94442;">ELIMINAR</button>
                    </div>
                </form>
            </div>

            <div class="card upload-card">
                <div class="upload-icon">📁</div>
                <h3>Importar Excel</h3>
                <p>Sube tu archivo <b>.xlsx</b> o <b>.csv</b>. Se leerán los datos y se guardarán automáticamente.</p>
                <form action="importar_excel.php" method="POST" enctype="multipart/form-data" style="width: 100%; display: flex; flex-direction: column; align-items: center;">
                    <input type="file" name="archivo_excel" accept=".xlsx, .csv" required style="color: var(--text-main); font-size: 13px; margin-bottom: 20px; width: 100%;">
                    <button type="submit" class="btn btn-primary" style="width: 80%;">SUBIR Y GUARDAR</button>
                </form>
            </div>
        </div>
    </div>

    <!-- VISTA 2: LISTA DE USUARIOS CON BOTONES DE DESCARGA -->
    <div id="vista-lista" class="vista">
        <div class="table-container">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; flex-wrap: wrap; gap: 15px;">
                <h2 style="margin: 0; border: none;">> Directorio de Usuarios</h2>
                
                <!-- BOTONES DE DESCARGA -->
                <div class="btn-group" style="margin-top: 0;">
                    <a href="exportar.php" class="btn btn-primary" style="background: #217346; border-color: #217346; color: white;">📊 Descargar Excel</a>
                    <a href="reporte_pdf.php" target="_blank" class="btn btn-primary" style="background: #a94442; border-color: #a94442; color: white;">📄 Descargar PDF</a>
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Cédula</th>
                        <th>Nombres</th>
                        <th>Apellidos</th>
                        <th>Teléfono</th>
                        <th>Fecha de Registro</th>
                    </tr>
                </thead>
                <tbody id="cuerpo-tabla">
                    <tr><td colspan="5" style="text-align:center;">Cargando datos...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<script>
    // 1. Manejo de las vistas
    function mostrarFormulario() {
        document.getElementById('vista-formulario').classList.add('activa');
        document.getElementById('vista-lista').classList.remove('activa');
        document.getElementById('btn-form').classList.add('active');
        document.getElementById('btn-lista').classList.remove('active');
    }

    function mostrarLista() {
        document.getElementById('vista-formulario').classList.remove('activa');
        document.getElementById('vista-lista').classList.add('activa');
        document.getElementById('btn-lista').classList.add('active');
        document.getElementById('btn-form').classList.remove('active');
        
        cargarUsuarios(); // Llama a la API para llenar la tabla
    }

    // 2. Cargar datos a la tabla desde Render
    function cargarUsuarios() {
        const tbody = document.getElementById('cuerpo-tabla');
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Cargando datos desde la nube...</td></tr>';

        fetch('https://otra-vez-o7oo.onrender.com/lista_usuarios')
            .then(response => response.json())
            .then(data => {
                tbody.innerHTML = '';
                if(data.exito && data.datos.length > 0) {
                    data.datos.forEach(user => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td><strong>${user.cedula}</strong></td>
                            <td>${user.nombre1} ${user.nombre2 || ''}</td>
                            <td>${user.apellido1} ${user.apellido2 || ''}</td>
                            <td>${user.telefono || '-'}</td>
                            <td>${user.fecha_registro || 'Desconocida'}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                } else {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No hay usuarios registrados aún.</td></tr>';
                }
            })
            .catch(error => {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:red;">Error al conectar (El servidor puede estar despertando).</td></tr>';
            });
    }

    // 3. Lógica de Congelar Pantalla
    function congelarPantalla() {
        document.getElementById('lock-screen').style.display = 'flex';
        document.getElementById('unlock-pass').value = '';
        document.getElementById('unlock-pass').focus();
    }

    function desbloquear() {
        const pass = document.getElementById('unlock-pass').value;
        if (pass === '1234') {
            document.getElementById('lock-screen').style.display = 'none';
        } else {
            alert('Contraseña incorrecta. El sistema sigue bloqueado.');
        }
    }

    // 4. Auto-cierre por inactividad (2 minutos)
    let tiempoInactividad;
    const TIEMPO_LIMITE = 120000; // 2 minutos

    function reiniciarTemporizador() {
        clearTimeout(tiempoInactividad);
        tiempoInactividad = setTimeout(cerrarSesionPorInactividad, TIEMPO_LIMITE);
    }

    function cerrarSesionPorInactividad() {
        window.location.href = "logout.php";
    }

    window.onload = reiniciarTemporizador;
    document.onmousemove = reiniciarTemporizador;
    document.onkeypress = reiniciarTemporizador;
    document.onclick = reiniciarTemporizador;
    document.onscroll = reiniciarTemporizador;
</script>

</body>
</html>
