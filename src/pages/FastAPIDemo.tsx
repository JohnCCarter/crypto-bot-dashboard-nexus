import React from 'react';
import { FastAPIUserDataDemo } from '../components/FastAPIUserDataDemo';

export const FastAPIDemo: React.FC = () => {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">FastAPI WebSocket Demo</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h2 className="text-xl font-semibold mb-4">User Data Stream</h2>
          <FastAPIUserDataDemo />
        </div>
        
        <div>
          <h2 className="text-xl font-semibold mb-4">FastAPI Information</h2>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-medium mb-2">Om FastAPI-migrationen</h3>
            <p className="mb-4">
              Detta är en demonstration av WebSocket-funktionalitet i FastAPI-migrationen.
              FastAPI-servern körs på port 8001.
            </p>
            
            <h3 className="text-lg font-medium mb-2">Fördelar med FastAPI</h3>
            <ul className="list-disc pl-5 space-y-1">
              <li>Asynkron hantering av anslutningar</li>
              <li>Bättre prestanda och skalbarhet</li>
              <li>Inbyggt WebSocket-stöd</li>
              <li>Automatisk API-dokumentation</li>
              <li>Pydantic-validering</li>
            </ul>
            
            <h3 className="text-lg font-medium mt-4 mb-2">WebSocket-endpoints</h3>
            <code className="block bg-gray-100 p-2 rounded">
              ws://localhost:8001/ws/market/{'{client_id}'}
            </code>
            <p className="text-sm text-gray-600 mt-1 mb-3">
              För marknadsdata (ticker, orderbook, trades)
            </p>
            
            <code className="block bg-gray-100 p-2 rounded">
              ws://localhost:8001/ws/user/{'{client_id}'}
            </code>
            <p className="text-sm text-gray-600 mt-1">
              För användardata (balances, orders, positions)
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}; 