import { Navigate, Route, Routes } from 'react-router-dom'
import { keycloakHabilitado } from './auth/keycloak'
import Ajustes from './paginas/Ajustes'
import Guia from './paginas/Guia'
import GuiaItem from './paginas/GuiaItem'
import Inicio from './paginas/Inicio'
import MeusEnxovais from './paginas/MeusEnxovais'
import NaoEncontrada from './paginas/NaoEncontrada'
import Planilha from './paginas/Planilha'
import Questionario from './paginas/Questionario'
import Roteiro from './paginas/Roteiro'
import Seguranca from './paginas/Seguranca'
import MinhaConta from './paginas/MinhaConta'

export function AppRoutes() {
  return (
    <Routes>
      {/*
        Raiz: com auth → lista de enxovais; sem auth → landing page.
        O AuthProvider com onLoad='login-required' já redireciona para o
        Keycloak se não autenticado, portanto /meus-enxovais é acessível
        apenas após login quando auth está habilitada.
      */}
      <Route
        path="/"
        element={
          keycloakHabilitado ? (
            <Navigate to="/meus-enxovais" replace />
          ) : (
            <Inicio />
          )
        }
      />
      <Route path="/meus-enxovais" element={<MeusEnxovais />} />
      <Route path="/minha-conta" element={<MinhaConta />} />
      <Route path="/questionario/:passo" element={<Questionario />} />
      <Route path="/enxoval/:id/planilha" element={<Planilha />} />
      <Route path="/enxoval/:id/roteiro" element={<Roteiro />} />
      <Route path="/enxoval/:id/guia" element={<Guia />} />
      <Route path="/enxoval/:id/guia/:item" element={<GuiaItem />} />
      <Route path="/enxoval/:id/seguranca" element={<Seguranca />} />
      <Route path="/enxoval/:id/ajustes" element={<Ajustes />} />
      <Route path="*" element={<NaoEncontrada />} />
    </Routes>
  )
}
