import asyncio
from discopy import closed
from widip.widish import SHELL_RUNNER, Constant, Process
from widip.computer import Language
from widip.async_ import unwrap

async def main():
    # Setup Gamma (dom=Ty())
    gamma = Constant(dom=closed.Ty())
    # Setup Id(IO)
    id_box = closed.Id(Language)
    
    # Diagram Gamma @ Id
    diagram = gamma @ id_box
    
    print(f"Diagram dom: {diagram.dom}, cod: {diagram.cod}")
    
    # Compiler/Runner
    # SHELL_RUNNER handles diagram -> Process
    process = SHELL_RUNNER(diagram)
    
    print(f"Process dom: {process.dom}, cod: {process.cod}")

    # Run process with input
    input_val = "some_input"
    res = await unwrap(process(input_val))
    
    print(f"Result: {res}")
    
    # Check decomposition
    # Gamma should return ("bin/widish",)
    # Id should return ("some_input",)
    # Result should be ("bin/widish", "some_input")

if __name__ == "__main__":
    asyncio.run(main())
