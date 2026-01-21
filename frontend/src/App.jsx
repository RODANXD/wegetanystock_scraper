import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import cleaned_products from './data/cleaned_products.json'
import Productlist from './components/Productlist'
function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <div>

        <Productlist />
      </div>
    </>
  )
}

export default App
