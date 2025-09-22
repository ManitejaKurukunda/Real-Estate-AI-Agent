import re
import openai
import pandas as pd
import numpy as np
from src.database.enhanced_connection import EnhancedDatabaseConnection
import os
import warnings
import json
from datetime import datetime
warnings.filterwarnings('ignore')
from config.system_prompts import PORTFOLIO_REPORT_PATTERNS, QUARTER_DATE_MAPPINGS, BASE_SYSTEM_PROMPT, SQL_GENERATION_RULES, COMMON_SQL_PATTERNS, BUSINESS_INSIGHTS_PROMPT, CASUAL_RESPONSES, DETAILED_REPORT_PATTERNS, SQL_VALIDATION_RULES, CONTEXT_AWARE_SQL_RULES, YEARLY_AGGREGATION_PATTERNS, AGGREGATION_RULES, DEBT_REPORT_PATTERNS, FACT_TABLE_DATE_COLUMNS

class PortfolioChatAgent:
    """
    Enhanced Real Estate AI - Portfolio Chat Agent
    Full data model awareness with conversation memory and intelligent SQL generation
    """
    
    def __init__(self, openai_api_key):
        # Set OpenAI API key
        openai.api_key = openai_api_key
        
        # Initialize database connection
        self.db = EnhancedDatabaseConnection()
        
        # Load complete data model for intelligence
        self.data_model = self._load_data_model()
        
        # Create comprehensive system prompt with full data model
        self.system_prompt = self._create_system_prompt()
        
        # Conversation memory for context tracking
        self.conversation_memory = []
        self.last_query_result = None
        self.last_sql_query = None
        self.last_question = None
        
        # Common spelling corrections
        self.spelling_corrections = {
            'liost': 'list', 'lsit': 'list', 'lst': 'list',
            'porofolio': 'portfolio', 'portoflio': 'portfolio', 'portifolio': 'portfolio',
            'propertys': 'properties', 'proprties': 'properties',
            'aseets': 'assets', 'asets': 'assets',
            'reveune': 'revenue', 'revenu': 'revenue',
            'expnese': 'expense', 'expenes': 'expenses',
            'hopsitality': 'hospitality', 'hopitality': 'hospitality',
            'multifamly': 'multifamily', 'multifmaily': 'multifamily',
            'qaurter': 'quarter', 'quater': 'quarter',
            'finacial': 'financial', 'fianncial': 'financial'
        }
        
                
        print("✅ Portfolio Chat Agent initialized with full data model awareness")
    
    def _load_data_model(self):
        """Load complete data model for intelligent query generation"""
        try:
            docs_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docs')
            with open(os.path.join(docs_path, 'data_model.json'), 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load data model: {e}")
            return {}
    
    def _create_system_prompt(self):
        """Create comprehensive system prompt with full data model context"""
        base_prompt = BASE_SYSTEM_PROMPT
        
        if not self.data_model:
            return base_prompt + "Database contains standard real estate tables."
        
        # Add complete table and column information
        tables_info = "COMPLETE DATABASE SCHEMA:\n\n"
        
        # Add dimension tables with full details
        for table_name, table_info in self.data_model.get('dimension_tables', {}).items():
            tables_info += f"{table_name}:\n"
            for col in table_info.get('columns', []):
                tables_info += f"  - {col['name']} ({col['type']}): {col['business_meaning']}\n"
            tables_info += f"  Purpose: {table_info.get('business_purpose', '')}\n\n"
        
        # Add fact tables with full details
        for table_name, table_info in self.data_model.get('fact_tables', {}).items():
            tables_info += f"{table_name}:\n"
            for measure in table_info.get('measures', []):
                tables_info += f"  - {measure['name']} ({measure['type']}): {measure['description']}\n"
            tables_info += f"  Purpose: {table_info.get('business_purpose', '')}\n\n"
        
        # Add business rules
        business_rules = "\nBUSINESS RULES:\n"
        for rule_category, rules in self.data_model.get('business_rules', {}).items():
            business_rules += f"{rule_category}:\n"
            for rule_name, rule_desc in rules.items():
                business_rules += f"  - {rule_name}: {rule_desc}\n"
            business_rules += "\n"
        
        # Add key relationships
        relationships = "\nKEY RELATIONSHIPS:\n"
        key_rels = self.data_model.get('key_relationships', {})
        for rel_name, rel_desc in key_rels.items():
            if isinstance(rel_desc, dict):
                relationships += f"- {rel_name}:\n"
                for ts_key, ts_val in rel_desc.items():
                    relationships += f"    * {ts_key}: {ts_val}\n"
            else:
                relationships += f"- {rel_name}: {rel_desc}\n"
        
        return base_prompt + tables_info + business_rules + relationships
    
    def chat(self, user_question):
        """
        Enhanced chat function with conversation memory and context awareness
        """
        try:
            # Store the question
            self.last_question = user_question
            
            # Correct spelling mistakes
            corrected_question = self._correct_spelling(user_question)
            
            # Add to conversation memory
            self.conversation_memory.append({"role": "user", "content": corrected_question})
            
            # Check for follow-up requests (show all, expand, etc.)
            if self._is_followup_request(corrected_question):
                return self._handle_followup_request(corrected_question)
            
            # Check if this is a casual greeting or conversation
            if self._is_casual_conversation(corrected_question):
                return self._handle_casual_conversation(corrected_question)
            
            # Check if this requires database query
            if self._needs_database_query(corrected_question):
                return self._handle_database_query(corrected_question)
            else:
                return self._handle_general_question(corrected_question)
                
        except Exception as e:
            return {"success": False, "error": f"Error processing question: {str(e)}"}
    
    def _is_followup_request(self, question):
        """Check if this is a follow-up request for more data"""
        followup_keywords = [
            'show all', 'all results', 'show everything', 'full table', 'complete list',
            'expand', 'show more', 'show rest', 'all rows', 'entire list', 'full results',
            'without limit', 'show complete', 'all data', 'everything'
        ]
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in followup_keywords)
    
    def _is_context_dependent_query(self, question):
        """Check if query depends on previous results"""
        context_indicators = [
            'above', 'previous', 'those', 'these', 'last', 
            'from the', 'in the results', 'that you showed',
            'filter', 'only show', 'just the', 'sort', 'order',
            'with respect to', 'by', 'according to'
        ]
        question_lower = question.lower()
        return any(indicator in question_lower for indicator in context_indicators) and self.last_sql_query is not None


    def _handle_followup_request(self, question):
        """Handle follow-up requests to show complete results"""
        try:
            if not self.last_sql_query:
                return {
                    "success": False,
                    "error": "No previous query to expand. Please ask a specific question first."
                }
            
            # Remove any TOP limitations from the last query
            expanded_query = self._remove_query_limits(self.last_sql_query)
            
            # Execute the expanded query
            if not self.db.connect():
                return {"success": False, "error": "Database connection failed"}
            
            print(f"Executing expanded query: {expanded_query}")
            query_df = self.db.execute_query(expanded_query)
            
            if query_df is None:
                return {"success": False, "error": "Expanded query execution failed"}
            
            # Store the complete result
            self.last_query_result = query_df.copy()
            self.last_sql_query = expanded_query
            
            self.db.close()
            
            insights = f"Showing complete results for your previous question: '{self.last_question}'. Found {len(query_df)} total rows."
            
            if len(query_df) > 50:
                insights += f"\n\n📊 **Large Dataset**: This query returned {len(query_df)} rows. All data is included below."
            
            return {
                "success": True,
                "question": question,
                "sql_query": expanded_query,
                "data": query_df,
                "insights": insights,
                "row_count": len(query_df)
            }
            
        except Exception as e:
            if self.db.connection:
                self.db.close()
            return {"success": False, "error": f"Follow-up request failed: {str(e)}"}
    
    def _remove_query_limits(self, sql_query):
        """Remove TOP limitations from SQL query"""
        import re
        # Remove TOP n clauses
        sql_query = re.sub(r'TOP\s+\d+\s*', '', sql_query, flags=re.IGNORECASE)
        return sql_query.strip()
    
    def _correct_spelling(self, text):
        """Correct common spelling mistakes"""
        corrected = text
        for mistake, correction in self.spelling_corrections.items():
            corrected = corrected.replace(mistake, correction)
        return corrected
    
    def _is_casual_conversation(self, question):
        """Check if this is casual conversation"""
        import re
        
        # Define casual patterns with word boundaries to avoid false matches
        casual_patterns = [
            r'\bhey\b', r'\bhi\b', r'\bhello\b', 
            r'\bgood morning\b', r'\bgood afternoon\b',
            r'\bthanks\b', r'\bthank you\b', 
            r'\bbye\b', r'\bgoodbye\b'
        ]
        
        question_lower = question.lower().strip()
        
        # Only consider it casual if:
        # 1. It matches a casual pattern with word boundaries
        # 2. The question is short and not asking for data
        if len(question_lower.split()) <= 5:
            for pattern in casual_patterns:
                if re.search(pattern, question_lower):
                    # Double-check it's not asking for data
                    data_keywords = ['show', 'list', 'get', 'find', 'properties', 'noi', 'data', 'assets']
                    if not any(keyword in question_lower for keyword in data_keywords):
                        return True
        
        return False
    
    def _needs_database_query(self, question):
        """Enhanced logic to determine if question needs database query"""
        data_keywords = [
            'show', 'list', 'get', 'find', 'what', 'which', 'how many', 'how much', 'total', 'sum', 'average',
            'properties', 'assets', 'funds', 'investors', 'revenue', 'noi', 'debt', 'equity',
            'performance', 'returns', 'cities', 'table', 'column', 'schema', 'irr', 'moic',
            'occupancy', 'expenses', 'cash flow', 'sale', 'acquisition', 'lender', 'borrower',
            'count', 'calculate', 'analyze', 'compare', 'filter', 'report', 'portfolio', 'summary',
            'q1', 'q2', 'q3', 'q4', 'quarter', 'year', 'ytd', 'monthly', 'detail', 'overview',
            'company', 'our', 'performance', 'metrics', 'kpi', 'dashboard',
            'above', 'previous', 'again', 'date', 'format', 'display', 'results', 'values'
        ]
        
        question_lower = question.lower()
        
        # Check if this is a follow-up request about previous results
        if self.last_sql_query and any(word in question_lower for word in ['above', 'previous', 'again', 'results', 'date']):
            return True
        
        return any(keyword in question_lower for keyword in data_keywords)
    
    def _handle_casual_conversation(self, question):
        """Handle casual conversation"""
        try:
            casual_responses = CASUAL_RESPONSES
            
            question_lower = question.lower().strip()
            
            # Check for specific responses
            for key, response in casual_responses.items():
                if key in question_lower:
                    return {
                        "success": True,
                        "question": question,
                        "insights": response,
                        "data": pd.DataFrame(),
                        "row_count": 0,
                        "sql_query": "No database query needed",
                        "conversation_type": "casual"
                    }
            
            # Default casual response
            return {
                "success": True,
                "question": question,
                "insights": "Hello! I'm your Real Estate AI assistant. I can help you analyze your portfolio of 12 properties across different sectors. What would you like to know?",
                "data": pd.DataFrame(),
                "row_count": 0,
                "sql_query": "No database query needed",
                "conversation_type": "casual"
            }
            
        except Exception as e:
            return {
                "success": True,
                "question": question,
                "insights": "Hello! I'm here to help with your real estate portfolio analysis. What would you like to know?",
                "data": pd.DataFrame(),
                "row_count": 0,
                "sql_query": "No database query needed",
                "conversation_type": "casual"
            }
    
    def _handle_database_query(self, question):
        """Enhanced database query handling with full context awareness"""
        try:
            # Connect to database
            if not self.db.connect():
                return {"success": False, "error": "Database connection failed"}
            
            # Generate SQL query with full context
            sql_query = self._generate_intelligent_sql(question)
            
            if not sql_query or "not possible" in sql_query.lower():
                return {"success": False, "error": "Could not generate a valid SQL query for this question. Try being more specific."}
            
            # Clean and execute query
            cleaned_query = self._clean_sql_query(sql_query)
            
            print(f"Executing SQL: {cleaned_query}")
            
            query_df = self.db.execute_query(cleaned_query)
            
            if query_df is None:
                return {"success": False, "error": "Query execution failed. Please check the query syntax."}
            
            # Store result for potential follow-up questions
            self.last_query_result = query_df.copy() if len(query_df) > 0 else pd.DataFrame()
            self.last_sql_query = cleaned_query
            
            if len(query_df) == 0:
                return {
                    "success": True,
                    "question": question,
                    "insights": "No data found for your query. The database might not contain the specific information you're looking for, or the filters might be too restrictive.",
                    "data": pd.DataFrame(),
                    "row_count": 0,
                    "sql_query": cleaned_query
                }
            
            # Generate insights
            insights = self._generate_business_insights(question, query_df)
            
            # Add follow-up suggestion if results were limited
            if 'TOP ' in cleaned_query.upper() and len(query_df) >= 10:
                insights += f"\n\n💡 **Tip**: This shows the first {len(query_df)} results. Ask 'show all results' to see everything!"
            
            # Add to conversation memory
            self.conversation_memory.append({
                "role": "assistant", 
                "content": f"Query returned {len(query_df)} results from {question}"
            })
            
            self.db.close()
            
            return {
                "success": True,
                "question": question,
                "sql_query": cleaned_query,
                "data": query_df,
                "insights": insights,
                "row_count": len(query_df)
            }
            
        except Exception as e:
            if self.db.connection:
                self.db.close()
            return {"success": False, "error": f"Database query failed: {str(e)}"}
    
    def _generate_intelligent_sql(self, question):
        """Generate SQL with complete data model intelligence and conversation context"""
        try:

            import re  # Import at method level to ensure availability
            # Check if this is an edited/rerun query by looking at conversation context
            is_edited_query = False
            if len(self.conversation_memory) > 0:
                # Check if we're rerunning a previous query
                for msg in self.conversation_memory[-5:]:
                    if msg.get('role') == 'user' and msg.get('content', '').lower().strip() == question.lower().strip():
                        is_edited_query = True
                        break
            
            # ALWAYS use OpenAI API for edited queries to ensure they get proper SQL generation
            if is_edited_query:
                print(f"🔄 Detected edited/rerun query: '{question}' - using OpenAI API")
                # Skip the simple SQL patterns and go straight to OpenAI
            else:
                # Simple SQL for common queries to avoid API calls
                question_lower = question.lower()
                
                # Top performing assets
                if 'top' in question_lower and 'performing' in question_lower:
                    import re
                    limit = 5
                    numbers = re.findall(r'\d+', question)
                    if numbers:
                        limit = int(numbers[0])
                    return f"""SELECT TOP {limit} 
                        a.AssetName,
                        a.PropertyType,
                        a.City,
                        a.State,
                        SUM(ao.NetOperatingIncome) as TotalNOI,
                        SUM(ao.TotalRevenue) as TotalRevenue,
                        AVG(ao.PhysicalOccupancy) as AvgOccupancy
                    FROM FactAssetOperations ao
                    JOIN DimAsset a ON ao.AssetID = a.AssetID
                    GROUP BY a.AssetName, a.PropertyType, a.City, a.State
                    ORDER BY TotalNOI DESC"""
                
                # Fund equity
                elif 'equity' in question_lower and 'fund' in question_lower:
                    return """SELECT 
                        f.FundName,
                        SUM(fi.InvestmentAmount) as TotalEquity
                    FROM FactInvestment fi
                    JOIN DimFund f ON fi.FundID = f.FundID
                    GROUP BY f.FundName
                    ORDER BY TotalEquity DESC"""
                
                # All properties
                elif 'all properties' in question_lower or 'show properties' in question_lower or 'show me all properties' in question_lower:
                    return """SELECT 
                        AssetName,
                        PropertyType,
                        City,
                        State,
                        AssetStatus
                    FROM DimAsset 
                    ORDER BY AssetName"""
                
                # Cities
                elif 'cities' in question_lower or 'what cities' in question_lower:
                    return """SELECT DISTINCT 
                        City,
                        State,
                        COUNT(*) as PropertyCount
                    FROM DimAsset 
                    WHERE City IS NOT NULL
                    GROUP BY City, State 
                    ORDER BY PropertyCount DESC"""
                
                # Total debt
                elif 'total debt' in question_lower or 'outstanding debt' in question_lower:
                    return """SELECT 
                        SUM(CurrentBalance) as TotalDebt,
                        COUNT(*) as NumberOfLoans,
                        AVG(InterestRate) as AvgInterestRate
                    FROM FactDebtIssued 
                    WHERE DebtStatus = 'Current'"""
                
                # Multifamily properties
                elif 'multifamily' in question_lower:
                    return """SELECT 
                        AssetID,
                        AssetName,
                        PropertyType,
                        City,
                        State,
                        NumberOfUnits,
                        TotalSquareFootage,
                        AssetStatus
                    FROM DimAsset 
                    WHERE PropertyType = 'Multifamily' 
                    ORDER BY AssetName"""
                
                # Hospitality properties
                elif 'hospitality' in question_lower:
                    return """SELECT 
                        AssetID,
                        AssetName,
                        PropertyType,
                        PropertySubType,
                        City,
                        State,
                        NumberOfUnits,
                        AssetStatus
                    FROM DimAsset 
                    WHERE PropertyType = 'Hospitality' 
                    ORDER BY AssetName"""
                
                # Property types
                elif 'property types' in question_lower or 'what property types' in question_lower:
                    return """SELECT DISTINCT 
                        PropertyType,
                        COUNT(*) as Count
                    FROM DimAsset
                    GROUP BY PropertyType
                    ORDER BY Count DESC"""
                
                # High NOI properties
                elif ('noi' in question_lower or 'net operating income' in question_lower) and ('high' in question_lower or 'top' in question_lower):
                    return """SELECT TOP 10
                        a.AssetName,
                        a.PropertyType,
                        ao.NetOperatingIncome as NOI,
                        ao.ReportingDateKey
                    FROM FactAssetOperations ao
                    JOIN DimAsset a ON ao.AssetID = a.AssetID
                    WHERE ao.NetOperatingIncome IS NOT NULL
                    ORDER BY ao.NetOperatingIncome DESC"""
                
                # Properties by acquisition price
                elif 'acquisition' in question_lower and 'price' in question_lower:
                    return """SELECT 
                        AssetName,
                        PropertyType,
                        City,
                        State,
                        AcquisitionPrice,
                        AcquisitionDate
                    FROM DimAsset
                    WHERE AcquisitionPrice IS NOT NULL
                    ORDER BY AcquisitionPrice DESC"""
                
                # Check for queries that combine multiple property types
                elif ('commercial' in question_lower and 'hospitality' in question_lower) or \
                     ('all' in question_lower and any(pt in question_lower for pt in ['commercial', 'hospitality', 'multifamily', 'retail'])):
                    # This needs OpenAI to generate proper UNION or WHERE clauses
                    print(f"📊 Complex multi-property query detected: '{question}' - using OpenAI API")
                    # Fall through to OpenAI generation
                else:
                    # For any other query, use OpenAI
                    print(f"🤖 Using OpenAI API for: '{question}'")
            
            # Otherwise, continue with normal GPT-4 generation
            # Create context from conversation memory
            conversation_context = ""
            if len(self.conversation_memory) > 1:
                conversation_context = "Recent conversation:\n" + "\n".join([
                    f"{msg['role']}: {msg['content'][:100]}..." 
                    for msg in self.conversation_memory[-4:]
                ])
            
            # Check if this is asking to filter previous results
            previous_context = ""
            is_date_format_request = any(word in question.lower() for word in ['date', 'format', 'display', 'show as date', 'readable'])
            is_sorting_request = any(phrase in question.lower() for phrase in ['with respect to', 'sort by', 'order by', 'based on'])
            
            if self.last_sql_query and (any(word in question.lower() for word in ['above', 'previous', 'those', 'these', 'last', 'again']) or is_date_format_request or is_sorting_request):
                # Extract base query without ORDER BY
                base_query = self.last_sql_query
                order_by_match = re.search(r'ORDER BY.*$', base_query, re.IGNORECASE | re.DOTALL)
                if order_by_match:
                    base_query = base_query[:order_by_match.start()].strip()
                
                previous_context = f"""
                IMPORTANT: The user is asking to modify the previous query results.
                Previous full query was: {self.last_sql_query}
                Base query without ORDER BY: {base_query}
                
                User's new request: {question}
                
                Context-Dependent Query Rules:
                1. If user says "above list" or "previous results", they mean the data from the last query
                2. If user says "with respect to X" or "sort by X", add ORDER BY X to the base query
                3. Keep ALL existing columns, JOINs, WHERE clauses intact - only modify ORDER BY
                
                Column Mapping for Sorting:
                - "current value", "valuation", "value" → Use CurrentValuation 
                - "price", "acquisition price" → Use AcquisitionPrice
                - "size", "square footage" → Use TotalSquareFootage
                - "units", "number of units" → Use NumberOfUnits
                - "date", "acquisition date" → Use AcquisitionDate
                - "name", "property name" → Use AssetName
                - "type" → Use PropertyType
                - "city" → Use City
                - "state" → Use State
               
                
                CRITICAL: Generate the COMPLETE query with the new ORDER BY clause.
                Do not generate partial queries or just the ORDER BY clause.
                
                Example:
                If base query is: SELECT * FROM DimAsset
                And user says: "sort by price value"
                Generate: SELECT * FROM DimAsset ORDER BY AcquisitionPrice DESC
                
                If they're asking about date formatting:
                1. Keep the existing JOINs and base structure
                2. For integer date keys (IssuanceDateKey, MaturityDateKey), convert them to readable dates
                3. Use this pattern: CONVERT(DATE, CONVERT(VARCHAR(8), DateKey), 112) AS DateFieldName
                4. Example: CONVERT(DATE, CONVERT(VARCHAR(8), IssuanceDateKey), 112) AS IssuanceDate
                5. Replace the integer date columns with formatted date columns in the SELECT clause
                """
            
            # Enhanced SQL generation prompt with full data model
            sql_prompt = f"""
            Generate a SQL Server query for: "{question}"
            
            CRITICAL CONTEXT HANDLING:
            - If {{previous_context}} contains information, this is a MODIFICATION of a previous query
            - You MUST use the base query provided and only modify as requested
            - For "with respect to", "sort by", "order by" requests, keep the exact same SELECT and FROM
            - Only add or modify the ORDER BY clause based on the column mapping provided
            
            {previous_context}
            
            {conversation_context}
            
            {SQL_GENERATION_RULES}
            
            {CONTEXT_AWARE_SQL_RULES}
            
            IMPORTANT: 
            - Always ensure string literals are properly closed with matching quotes
            - If user asks for date formatting, convert integer date keys to readable dates
            - Use CONVERT(DATE, CONVERT(VARCHAR(8), DateKey), 112) for date conversion
            - For queries asking for multiple property types (e.g., "commercial and hospitality"), use appropriate WHERE clauses or UNION
            - Example for multiple types: WHERE PropertyType IN ('Commercial', 'Hospitality')
            
            {self.system_prompt}
            
            
            {DEBT_REPORT_PATTERNS}
            
            {FACT_TABLE_DATE_COLUMNS}
            
            {YEARLY_AGGREGATION_PATTERNS}
            
            {AGGREGATION_RULES}
            
            {PORTFOLIO_REPORT_PATTERNS}
            
            {QUARTER_DATE_MAPPINGS}
            
            {SQL_VALIDATION_RULES}
            
            SQL Query:
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert SQL developer for real estate databases. Return only clean SQL queries without any formatting or explanations."},
                    {"role": "user", "content": sql_prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            sql_query = response.choices[0].message.content.strip()
            return sql_query
            
        except Exception as e:
            print(f"Error generating SQL: {e}")
            return None
    
    def _clean_sql_query(self, sql_query):
        """Clean and prepare SQL query for execution"""
        # Remove code blocks and quotes
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        sql_query = sql_query.strip('"').strip("'")
        
        # Ensure single statement
        if ";" in sql_query:
            sql_query = sql_query.split(";")[0]
        
        return sql_query.strip()
    
    def _handle_general_question(self, question):
        """Handle general questions about real estate"""
        try:
            general_prompt = f"""
            User asked: "{question}"
            
            This is a general question about real estate portfolio management. Provide a helpful response
            based on real estate knowledge and mention that specific portfolio data is available if needed.
            
            Available data includes properties, funds, investors, performance metrics, and financial data.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful real estate portfolio assistant."},
                    {"role": "user", "content": general_prompt}
                ],
                temperature=0.5,
                max_tokens=400
            )
            
            return {
                "success": True,
                "question": question,
                "insights": response.choices[0].message.content.strip(),
                "data": pd.DataFrame(),
                "row_count": 0,
                "sql_query": "No database query needed",
                "conversation_type": "general"
            }
            
        except Exception as e:
            return {"success": False, "error": f"Could not process general question: {str(e)}"}
    
    def _generate_business_insights(self, question, data_df):
        """Generate contextual business insights"""
        try:
            if len(data_df) == 0:
                return "No data found for your query."
            
            # Create intelligent summary
            data_summary = f"Query returned {len(data_df)} results with columns: {', '.join(data_df.columns.tolist())}."
            
            # Add sample values for context
            if len(data_df) > 0:
                # Get a few sample rows as dict for better context
                sample_rows = data_df.head(2).to_dict('records')
                data_summary += f" Sample data includes: {sample_rows}"
            
            insights_prompt = f"""
            User asked: "{question}"
            
            Query results: {data_summary}
            
            {BUSINESS_INSIGHTS_PROMPT}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a senior real estate analyst providing strategic insights."},
                    {"role": "user", "content": insights_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Query executed successfully and returned {len(data_df)} results with columns: {', '.join(data_df.columns.tolist())}"
    
    
    def get_ppt_recommendations(self, data, question, insights, custom_prompt, num_slides):
        """Get AI recommendations for PowerPoint structure and content"""
        try:
            # Convert data to summary for AI
            data_summary = ""
            if data:
                df = pd.DataFrame(data)
                data_summary = f"Data contains {len(df)} rows with columns: {', '.join(df.columns.tolist()[:10])}"
                
                # Add key statistics
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                for col in numeric_cols[:5]:
                    if 'revenue' in col.lower() or 'income' in col.lower():
                        data_summary += f"\nTotal {col}: ${df[col].sum():,.0f}"
                    elif 'occupancy' in col.lower():
                        data_summary += f"\nAverage {col}: {df[col].mean():.1f}%"
            
            ppt_prompt = f"""
            Create a professional PowerPoint presentation structure with {num_slides} slides.
            
            Context:
            - Original Question: {question}
            - Custom Requirements: {custom_prompt}
            - Data Summary: {data_summary}
            - Key Insights: {insights}
            
            Provide a detailed outline for each slide including:
            1. Slide title
            2. Key content points
            3. Recommended visualizations (chart types)
            4. Data to highlight
            
            Focus on creating a presentation that is:
            - Ready to present to executives
            - Visually appealing with appropriate charts
            - Data-driven with clear insights
            - Actionable with clear recommendations
            
            Format the response as a structured list of slides.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert presentation designer for real estate portfolios."},
                    {"role": "user", "content": ppt_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating PPT recommendations: {e}")
            return None

    
    def get_sample_questions(self):
        """Return intelligent sample questions based on data model"""
        return [
            "Hey, what can you help me with?",
            "Show me all properties in our portfolio",
            "What property types do we have?",
            "What cities do we have properties in?",
            "List all multifamily properties",
            "Show me hospitality properties",
            "Give me total equity for each fund",
            "What is our total outstanding debt?",
            "Show me properties with high NOI",
            "List properties by acquisition price"
        ]
