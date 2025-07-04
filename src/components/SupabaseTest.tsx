import React, { useEffect, useState } from "react";
import { supabase } from "../lib/supabaseClient";

export const SupabaseTest = () => {
  const [orders, setOrders] = useState<Array<{ id: string; symbol: string; amount: number }>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOrders = async () => {
      const { data, error } = await supabase
        .from("orders")
        .select("*")
        .limit(5);
      if (error) setError(error.message);
      else setOrders(data || []);
    };
    fetchOrders();
  }, []);

  return (
    <div>
      <h2>Supabase Orders Test</h2>
      {error && <div style={{ color: "red" }}>Fel: {error}</div>}
      <ul>
        {orders.map((order) => (
          <li key={order.id}>
            {order.id}: {order.symbol} - {order.amount}
          </li>
        ))}
      </ul>
      {!error && orders.length === 0 && <div>Inga ordrar hittades.</div>}
    </div>
  );
};