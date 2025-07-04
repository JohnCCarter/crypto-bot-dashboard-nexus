// Korrekt sätt att använda konfigurationen

const
 { createClient } = 
require
(
'@supabase/supabase-js'
);
const
 supabaseUrl = 
'https://ihqehxxyrtqnxuxknuvh.supabase.co'
;
const
 supabaseKey = 
'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlocWVoeHh5cnRxbnh1eGtudXZoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk4MTEyNDcsImV4cCI6MjA2NTM4NzI0N30.lNZJphM0JRqSaX2M_pT6gU8EsKx4yxNHAjxYY8_s4cc'
;
const
 supabase = createClient(supabaseUrl, supabaseKey);