var socket = io.connect("http://127.0.0.1:5000");
var usuario = document.getElementById("usuario_nombre")?.value;

if (usuario) {
  socket.emit("nuevo_usuario", { usuario: usuario });
}

socket.on("usuarios_conectados", function (lista) {
  let div = document.getElementById("usuarios-conectados");
  if (div) div.innerHTML = "<h4>Usuarios conectados:</h4>" + lista.join(", ");
});

socket.on("mensaje_chat", function (data) {
  let chat = document.getElementById("zona-chat");
  if (chat) chat.innerHTML += `<p><b>${data.usuario}:</b> ${data.mensaje}</p>`;
});
