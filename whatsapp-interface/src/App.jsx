import React from 'react';

function App() {
  return (
    // Contenedor principal (Fondo gris, pantalla completa, centrado)
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">

      {/* Tarjeta del Chat */}
      <div className="bg-white w-full max-w-md rounded-xl shadow-lg p-6">

        <h2 className="text-xl font-bold text-gray-800 mb-4">
          Chat con Cliente
        </h2>

        {/* Burbuja de chat del bot (Verde de WhatsApp) */}
        <div className="bg-green-100 border border-green-300 text-green-800 p-3 rounded-lg rounded-tr-none max-w-[80%] ml-auto mb-4 shadow-sm">
          <p className="text-sm">¡Hola! Soy el asistente virtual. ¿En qué puedo ayudarte hoy?</p>
          <span className="text-[10px] text-green-600 block text-right mt-1">10:42 AM - Bot IA</span>
        </div>

        {/* Burbuja de chat del humano (Gris) */}
        <div className="bg-gray-100 border border-gray-200 text-gray-800 p-3 rounded-lg rounded-tl-none max-w-[80%] mr-auto shadow-sm">
          <p className="text-sm">Necesito hablar con un agente humano, por favor.</p>
          <span className="text-[10px] text-gray-500 block mt-1">10:43 AM - Cliente</span>
        </div>

      </div>

    </div>
  );
}

export default App;