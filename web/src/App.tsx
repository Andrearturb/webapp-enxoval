import { Route, Routes } from 'react-router-dom'
import Ajustes from './paginas/Ajustes'
import Guia from './paginas/Guia'
import GuiaItem from './paginas/GuiaItem'
import Inicio from './paginas/Inicio'
import NaoEncontrada from './paginas/NaoEncontrada'
import Planilha from './paginas/Planilha'
import Questionario from './paginas/Questionario'
import Roteiro from './paginas/Roteiro'
import Seguranca from './paginas/Seguranca'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Inicio />} />
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
