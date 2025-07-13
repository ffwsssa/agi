# IQuote Demo System

This directory contains a self-contained demonstration of an AI-powered sales quoting system featuring two collaborating agents.

- **`solution_architect_agent.py`**: A centralized agent that provides technical networking solutions based on a product catalog.
- **`local_data_agent.py`**: A client agent that takes a business problem, gets the technical solution, and uses an LLM to refine it into a customer-friendly proposal.
- **`product_catalog.py`**: The data source for products, pricing, and use cases.

## Prerequisites

Ensure you have the required Python packages installed:

```bash
pip install uagents requests langchain-openai python-dotenv
```

You also need a functional `api_keys.py` file in the root of the project.

## How to Run the Demo (Happy Path)

Follow these steps to run the demo and see the agents in action.

### Step 1: Start the Centralized Solution Architect Agent

First, run the `solution_architect_agent.py`. This agent will wait for requests.

```bash
python IQuote/solution_architect_agent.py
```

When the agent starts, it will print its address to the console. It will look something like this:

`INFO:     Address: agent1q...`

**Copy this full agent address.** You will need it in the next step.

### Step 2: Configure the Local Data Agent

Open the file `IQuote/local_data_agent.py` in your editor.

Find the following line at the top of the file:

```python
SOLUTION_ARCHITECT_AGENT_ADDRESS = "agent1qft5z5m3d4r6d5hmn2nh4e7qg7qg3z4h9qgqgqgqgqgqgqgqgqgqgqg3"
```

**Paste the address you copied** from Step 1 into the quotes, replacing the placeholder address. Save the file.

### Step 3: Run the Local Data Agent

Now, in a **new terminal window**, run the `local_data_agent.py`:

```bash
python IQuote/local_data_agent.py
```

This agent will automatically send the pre-defined business problem to the solution architect agent.

### Step 4: View the Result

After a few moments, the local agent will receive the technical solution, process it with an LLM, and print the final, customer-friendly proposal to the console. The output will look similar to this:

```
============================================================
✅ Refined Customer Proposal:
============================================================
Hello,

Thank you for considering us for your networking needs as you expand your business with 10 new branches. Based on your requirements for a comprehensive solution including SD-WAN, switching, wireless, and robust security, we've put together a preliminary proposal designed for performance, security, and scalability.

Here’s a breakdown of the recommended solution and the value it brings to your business:

*   **CloudConnect SD-WAN M (SDW-2000):** This will be the backbone of your branch connectivity, ensuring reliable and secure access to your cloud applications. It provides high-speed throughput and comes with advanced security features built-in.
*   **NetSwitch 48-Port L3 (SW-48):** This powerful switch will manage your local branch network traffic efficiently, ensuring all your devices have fast and stable connections.
*   **And more...**

**Important Note on Pricing:**

The estimated cost provided is for a single branch. However, we offer significant volume discounts. By purchasing the solution for all 10 branches at once, you will benefit from reduced pricing per unit. We highly recommend this approach to maximize your return on investment.

We are confident this solution provides a solid foundation for your business growth. Let's schedule a brief call to discuss your specific needs in more detail and create a finalized, discounted quote for you.
============================================================
```

This completes the demo flow. 