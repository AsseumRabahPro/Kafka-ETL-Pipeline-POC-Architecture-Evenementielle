import psycopg
from datetime import datetime, timedelta
import json

DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'etl_db'
DB_USER = 'etl_user'
DB_PASSWORD = 'etl_password'

class OrderKPIs:
    """Calculer les KPIs à partir de la table de faits"""
    
    def __init__(self):
        try:
            self.conn = psycopg.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            self.cursor = self.conn.cursor()
        except psycopg.Error as e:
            print(f"[ERROR] Connection failed: {e}")
            raise
    
    def get_total_orders_by_day(self):
        """KPI 1: Nombre de commandes par jour"""
        query = """
            SELECT 
                order_date,
                COUNT(*) as total_orders,
                COUNT(CASE WHEN status = 'validated' THEN 1 END) as validated,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected
            FROM fact_orders
            GROUP BY order_date
            ORDER BY order_date DESC
            LIMIT 10
        """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        
        print("\n[STATS] KPI 1: NOMBRE DE COMMANDES PAR JOUR")
        print("=" * 80)
        print(f"{'Date':<12} {'Total':<8} {'[OK] Validated':<15} {'[ERROR] Rejected':<15}")
        print("-" * 80)
        
        total_all = 0
        for row in rows:
            date, total, validated, rejected = row
            print(f"{str(date):<12} {total:<8} {validated:<15} {rejected:<15}")
            total_all += total
        
        print("-" * 80)
        print(f"{'TOTAL':<12} {total_all:<8}")
    
    def get_total_amount_by_day(self):
        """KPI 2: Montant total par jour"""
        query = """
            SELECT 
                order_date,
                SUM(CASE WHEN status = 'validated' THEN amount ELSE 0 END) as validated_amount,
                SUM(CASE WHEN status = 'rejected' THEN amount ELSE 0 END) as rejected_amount,
                SUM(amount) as total_amount,
                AVG(CASE WHEN status = 'validated' THEN amount END) as avg_validated_amount
            FROM fact_orders
            GROUP BY order_date
            ORDER BY order_date DESC
            LIMIT 10
        """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        
        print("\n[MONEY] KPI 2: MONTANT TOTAL PAR JOUR (USD)")
        print("=" * 100)
        print(f"{'Date':<12} {'[OK] Validated':<18} {'[ERROR] Rejected':<18} {'Total':<18} {'Avg Validated':<18}")
        print("-" * 100)
        
        total_validated = 0
        total_rejected = 0
        
        for row in rows:
            date, val_amt, rej_amt, tot_amt, avg_amt = row
            val_amt = val_amt or 0
            rej_amt = rej_amt or 0
            tot_amt = tot_amt or 0
            avg_amt = avg_amt or 0
            
            print(f"{str(date):<12} ${val_amt:>16.2f} ${rej_amt:>16.2f} ${tot_amt:>16.2f} ${avg_amt:>16.2f}")
            
            total_validated += val_amt
            total_rejected += rej_amt
        
        print("-" * 100)
        print(f"{'TOTAL':<12} ${total_validated:>16.2f} ${total_rejected:>16.2f}")
    
    def get_rejection_rate(self):
        """KPI 3: Taux de rejet"""
        query = """
            SELECT 
                order_date,
                COUNT(*) as total_orders,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected,
                ROUND(
                    100.0 * COUNT(CASE WHEN status = 'rejected' THEN 1 END) / COUNT(*),
                    2
                ) as rejection_rate_percent
            FROM fact_orders
            GROUP BY order_date
            ORDER BY order_date DESC
            LIMIT 10
        """
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        
        print("\n[STATS] KPI 3: TAUX DE REJET")
        print("=" * 80)
        print(f"{'Date':<12} {'Total Orders':<15} {'Rejected':<12} {'Rejection Rate':<20}")
        print("-" * 80)
        
        overall_total = 0
        overall_rejected = 0
        
        for row in rows:
            date, total, rejected, rate = row
            print(f"{str(date):<12} {total:<15} {rejected:<12} {rate:>17.2f}%")
            overall_total += total
            overall_rejected += rejected
        
        print("-" * 80)
        if overall_total > 0:
            overall_rate = 100.0 * overall_rejected / overall_total
            print(f"{'OVERALL':<12} {overall_total:<15} {overall_rejected:<12} {overall_rate:>17.2f}%")
    
    def get_detailed_stats(self):
        """Statistiques détaillées"""
        query = """
            SELECT 
                COUNT(*) as total_orders,
                COUNT(CASE WHEN status = 'validated' THEN 1 END) as validated_count,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_count,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount,
                MIN(amount) as min_amount,
                MAX(amount) as max_amount,
                AVG(CASE WHEN items IS NOT NULL THEN items ELSE 0 END) as avg_items
            FROM fact_orders
        """
        self.cursor.execute(query)
        row = self.cursor.fetchone()
        
        print("\n[GOAL] STATISTIQUES GLOBALES")
        print("=" * 80)
        
        total, validated, rejected, total_amt, avg_amt, min_amt, max_amt, avg_items = row
        
        print(f"Total commandes:        {total:>10}")
        print(f"[OK] Validées:            {validated:>10} ({100*validated/total if total > 0 else 0:.1f}%)")
        print(f"[ERROR] Rejetées:            {rejected:>10} ({100*rejected/total if total > 0 else 0:.1f}%)")
        print(f"\nMontant total:          ${total_amt or 0:>9.2f}")
        print(f"Montant moyen:          ${avg_amt or 0:>9.2f}")
        print(f"Montant min/max:        ${min_amt or 0:>9.2f} / ${max_amt or 0:>9.2f}")
        print(f"\nNombre items moyen:     {avg_items or 0:>9.2f}")
        print("=" * 80)
    
    def run(self):
        """Exécuter tous les KPIs"""
        try:
            print("\n")
            print("█" * 80)
            print("█" + " " * 78 + "█")
            print("█" + " " * 20 + "[STATS] ORDER ANALYTICS DASHBOARD [STATS]" + " " * 25 + "█")
            print("█" + " " * 78 + "█")
            print("█" * 80)
            
            self.get_detailed_stats()
            self.get_total_orders_by_day()
            self.get_total_amount_by_day()
            self.get_rejection_rate()
            
            print("\n[OK] Dashboard updated at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
        except Exception as e:
            print(f"[ERROR] Error: {e}")
        finally:
            self.close()
    
    def close(self):
        """Fermer les connexions"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

if __name__ == '__main__':
    kpi = OrderKPIs()
    kpi.run()
