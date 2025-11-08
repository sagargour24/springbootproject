#!/usr/bin/env python3
"""
Layered VCF to Neo4j Loader
Modular architecture for Layer 2 Knowledge Graph
"""

import os
import sys
import time
import logging
import toml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from neo4j import GraphDatabase

# ============================================================================
# LAYER 1: CONFIGURATION
# ============================================================================

class Config:
    """Configuration management layer"""
    
    def __init__(self, config_file='config_simple.toml'):
        self.config = self._load_config(config_file)
        self.neo4j = self.config['neo4j']
        self.data = self.config['data']
        self.performance = self.config['performance']
    
    def _load_config(self, config_file):
        """Load configuration from TOML file"""
        if os.path.exists(config_file):
            return toml.load(config_file)
        else:
            # Default configuration
            return {
                'neo4j': {
                    'uri': 'bolt://localhost:7687',
                    'username': 'neo4j',
                    'password': 'genegenius'
                },
                'data': {
                    'vcf_directory': 'geneData',
                    'batch_size': 1000,
                    'max_variants_per_chromosome': None
                },
                'performance': {
                    'target_query_latency_ms': 100,
                    'min_graph_edges': 3000
                }
            }

# ============================================================================
# LAYER 2: MODELS (Domain Objects)
# ============================================================================

@dataclass
class Variant:
    """Variant domain model"""
    variant_id: str
    chromosome: str
    position: int
    reference: str
    alternate: str
    allele_frequency: Optional[float] = None
    gene: Optional[str] = None
    quality: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for Neo4j"""
        return {
            'variant_id': self.variant_id,
            'chromosome': self.chromosome,
            'position': self.position,
            'reference': self.reference,
            'alternate': self.alternate,
            'af': self.allele_frequency,
            'gene': self.gene,
            'quality': self.quality
        }

@dataclass
class Phenotype:
    """Phenotype domain model"""
    phenotype_id: str
    name: str
    source: str = 'Simulated'
    
    def to_dict(self) -> Dict:
        return {
            'phenotype_id': self.phenotype_id,
            'name': self.name,
            'source': self.source
        }

@dataclass
class Drug:
    """Drug domain model"""
    drug_id: str
    name: str
    source: str = 'FDA'
    
    def to_dict(self) -> Dict:
        return {
            'drug_id': self.drug_id,
            'name': self.name,
            'source': self.source
        }

# ============================================================================
# LAYER 3: DATA ACCESS (Repository Pattern)
# ============================================================================

class Neo4jRepository:
    """Data access layer for Neo4j operations"""
    
    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
    
    def close(self):
        """Close database connection"""
        self.driver.close()
    
    def clear_database(self):
        """Clear all data from database"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
    
    def create_indexes(self):
        """Create database indexes for performance"""
        with self.driver.session() as session:
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (v:Variant) ON (v.variant_id)",
                "CREATE INDEX IF NOT EXISTS FOR (v:Variant) ON (v.chromosome, v.position)",
                "CREATE INDEX IF NOT EXISTS FOR (p:Phenotype) ON (p.phenotype_id)",
                "CREATE INDEX IF NOT EXISTS FOR (d:Drug) ON (d.drug_id)",
                "CREATE INDEX IF NOT EXISTS FOR (o:Outcome) ON (o.outcome_id)"
            ]
            for index in indexes:
                session.run(index)
    
    def batch_create_variants(self, variants: List[Variant]) -> int:
        """Batch create variant nodes"""
        with self.driver.session() as session:
            query = """
                UNWIND $variants as v
                MERGE (variant:Variant {variant_id: v.variant_id})
                SET variant += v
                RETURN count(variant) as created
            """
            result = session.run(query, variants=[v.to_dict() for v in variants])
            return result.single()['created']
    
    def create_phenotypes(self, phenotypes: List[Phenotype]) -> int:
        """Create phenotype nodes"""
        with self.driver.session() as session:
            query = """
                UNWIND $phenotypes as p
                MERGE (phenotype:Phenotype {phenotype_id: p.phenotype_id})
                SET phenotype += p
                RETURN count(phenotype) as created
            """
            result = session.run(query, phenotypes=[p.to_dict() for p in phenotypes])
            return result.single()['created']
    
    def create_drugs(self, drugs: List[Drug]) -> int:
        """Create drug nodes"""
        with self.driver.session() as session:
            query = """
                UNWIND $drugs as d
                MERGE (drug:Drug {drug_id: d.drug_id})
                SET drug += d
                RETURN count(drug) as created
            """
            result = session.run(query, drugs=[d.to_dict() for d in drugs])
            return result.single()['created']
    
    def create_relationships(self, relationship_type: str, source_label: str, 
                           target_label: str, limit: int = 1000) -> int:
        """Create relationships between nodes"""
        with self.driver.session() as session:
            if relationship_type == "CAUSES":
                query = f"""
                    MATCH (s:{source_label})
                    WHERE s.af < 0.001 OR s.af IS NULL
                    WITH s LIMIT {limit}
                    MATCH (t:{target_label})
                    WITH s, t LIMIT 1
                    MERGE (s)-[r:CAUSES]->(t)
                    SET r.confidence = COALESCE(1 - s.af, 0.5),
                        r.source = 'Simulated'
                    RETURN count(r) as created
                """
            elif relationship_type == "TREATED_BY":
                query = f"""
                    MATCH (s:{source_label})
                    WITH s LIMIT {limit}
                    MATCH (t:{target_label})
                    WITH s, t LIMIT 1
                    MERGE (s)-[r:TREATED_BY]->(t)
                    SET r.efficacy = 'moderate',
                        r.source = 'Simulated'
                    RETURN count(r) as created
                """
            elif relationship_type == "PREDICTS":
                query = f"""
                    MATCH (s:{source_label})
                    WHERE s.af IS NOT NULL
                    WITH s LIMIT {limit}
                    MERGE (t:Outcome {{
                        outcome_id: s.variant_id + '_outcome',
                        prediction: CASE
                            WHEN s.af < 0.001 THEN 'High impact'
                            WHEN s.af < 0.01 THEN 'Moderate impact'
                            ELSE 'Low impact'
                        END
                    }})
                    MERGE (s)-[r:PREDICTS]->(t)
                    SET r.confidence = 1 - s.af,
                        r.source = 'Frequency-based'
                    RETURN count(r) as created
                """
            elif relationship_type == "RESULTS_IN":
                query = f"""
                    MATCH (s:{source_label})
                    WITH s LIMIT {limit}
                    MATCH (t:{target_label})
                    WITH s, t LIMIT 1
                    MERGE (s)-[r:RESULTS_IN]->(t)
                    SET r.effectiveness = 'positive',
                        r.confidence = 0.85,
                        r.source = 'Simulated'
                    RETURN count(r) as created
                """
            else:
                return 0
            
            result = session.run(query)
            return result.single()['created']
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        with self.driver.session() as session:
            query = """
                MATCH (v:Variant) WITH count(v) as variants
                MATCH (p:Phenotype) WITH variants, count(p) as phenotypes
                MATCH (d:Drug) WITH variants, phenotypes, count(d) as drugs
                MATCH (o:Outcome) WITH variants, phenotypes, drugs, count(o) as outcomes
                OPTIONAL MATCH ()-[r1:CAUSES]->() WITH variants, phenotypes, drugs, outcomes, count(r1) as causes
                OPTIONAL MATCH ()-[r2:TREATED_BY]->() WITH variants, phenotypes, drugs, outcomes, causes, count(r2) as treatments
                OPTIONAL MATCH ()-[r3:PREDICTS]->()
                WITH variants, phenotypes, drugs, outcomes, causes, treatments, count(r3) as predictions
                OPTIONAL MATCH ()-[r4:RESULTS_IN]->()
                RETURN variants, phenotypes, drugs, outcomes, causes, treatments, predictions, count(r4) as results
            """
            result = session.run(query).single()
            
            if result:
                return {
                    'nodes': {
                        'variants': result['variants'],
                        'phenotypes': result['phenotypes'],
                        'drugs': result['drugs'],
                        'outcomes': result['outcomes']
                    },
                    'relationships': {
                        'CAUSES': result['causes'],
                        'TREATED_BY': result['treatments'],
                        'PREDICTS': result['predictions'],
                        'RESULTS_IN': result['results'],
                        'total': result['causes'] + result['treatments'] + result['predictions'] + result['results']
                    }
                }
            return {}

# ============================================================================
# LAYER 4: SERVICES (Business Logic)
# ============================================================================

class VCFParserService:
    """Service for parsing VCF files"""
    
    def __init__(self):
        self.parser_type = self._detect_parser()
    
    def _detect_parser(self):
        """Detect available VCF parser"""
        try:
            import cyvcf2
            return 'cyvcf2'
        except ImportError:
            try:
                import pysam
                return 'pysam'
            except ImportError:
                print("ERROR: No VCF parser available. Install cyvcf2 or pysam")
                sys.exit(1)
    
    def parse_vcf(self, vcf_path: str, max_variants: Optional[int] = None):
        """Parse VCF file and yield Variant objects"""
        if self.parser_type == 'cyvcf2':
            yield from self._parse_with_cyvcf2(vcf_path, max_variants)
        else:
            yield from self._parse_with_pysam(vcf_path, max_variants)
    
    def _parse_with_cyvcf2(self, vcf_path: str, max_variants: Optional[int]):
        """Parse using cyvcf2"""
        import cyvcf2
        
        vcf = cyvcf2.VCF(vcf_path)
        count = 0
        
        for record in vcf:
            if max_variants and count >= max_variants:
                break
            
            if record.FILTER and record.FILTER != "PASS":
                continue
            
            # Extract allele frequency
            af = None
            if hasattr(record.INFO, 'get'):
                af_value = record.INFO.get('AF')
                if af_value:
                    af = float(af_value[0]) if isinstance(af_value, (list, tuple)) else float(af_value)
            
            for alt in record.ALT:
                yield Variant(
                    variant_id=f"{record.CHROM}:{record.POS}:{record.REF}:{alt}",
                    chromosome=str(record.CHROM),
                    position=record.POS,
                    reference=record.REF,
                    alternate=alt,
                    allele_frequency=af,
                    quality=record.QUAL
                )
                count += 1
    
    def _parse_with_pysam(self, vcf_path: str, max_variants: Optional[int]):
        """Parse using pysam"""
        import pysam
        
        vcf = pysam.VariantFile(vcf_path)
        count = 0
        
        for record in vcf:
            if max_variants and count >= max_variants:
                break
            
            # Extract allele frequency
            af = None
            if 'AF' in record.info:
                af_value = record.info['AF']
                if af_value:
                    af = float(af_value[0]) if isinstance(af_value, tuple) else float(af_value)
            
            for alt in (record.alts or []):
                yield Variant(
                    variant_id=f"{record.chrom}:{record.pos}:{record.ref}:{alt}",
                    chromosome=str(record.chrom),
                    position=record.pos,
                    reference=record.ref,
                    alternate=alt,
                    allele_frequency=af,
                    quality=record.qual
                )
                count += 1

class ClinicalDataService:
    """Service for clinical data (simulated)"""
    
    @staticmethod
    def get_phenotypes() -> List[Phenotype]:
        """Get simulated phenotypes"""
        return [
            Phenotype("PHENO_001", "Breast Cancer"),
            Phenotype("PHENO_002", "Cystic Fibrosis"),
            Phenotype("PHENO_003", "Alzheimer Disease"),
            Phenotype("PHENO_004", "Type 2 Diabetes"),
            Phenotype("PHENO_005", "Huntington Disease"),
        ]
    
    @staticmethod
    def get_drugs() -> List[Drug]:
        """Get simulated drugs"""
        return [
            Drug("DRUG_001", "Trastuzumab"),
            Drug("DRUG_002", "Ivacaftor"),
            Drug("DRUG_003", "Donepezil"),
            Drug("DRUG_004", "Metformin"),
            Drug("DRUG_005", "Tetrabenazine"),
        ]

class GraphBuilderService:
    """Service for building the knowledge graph"""
    
    def __init__(self, repository: Neo4jRepository, config: Config):
        self.repo = repository
        self.config = config
        self.vcf_parser = VCFParserService()
        self.clinical_service = ClinicalDataService()
    
    def build_graph(self, vcf_files: List[str], limit_per_file: Optional[int] = None):
        """Build complete knowledge graph"""
        print("\n" + "="*70)
        print(" BUILDING LAYER 2 KNOWLEDGE GRAPH")
        print("="*70)
        
        # Step 1: Setup
        print("\n1. Setting up database...")
        self.repo.clear_database()
        self.repo.create_indexes()
        
        # Step 2: Load variants
        print("\n2. Loading VCF variants...")
        total_variants = self._load_variants(vcf_files, limit_per_file)
        print(f"   Loaded {total_variants:,} variants")
        
        # Step 3: Load clinical data
        print("\n3. Loading clinical data...")
        self._load_clinical_data()
        
        # Step 4: Create relationships
        print("\n4. Creating relationships...")
        self._create_relationships()
        
        # Step 5: Verify
        print("\n5. Verifying compliance...")
        stats = self.repo.get_statistics()
        self._print_statistics(stats)
        
        return stats
    
    def _load_variants(self, vcf_files: List[str], limit_per_file: Optional[int]) -> int:
        """Load variants from VCF files"""
        total_loaded = 0
        batch_size = self.config.data['batch_size']
        
        for vcf_file in vcf_files:
            if not os.path.exists(vcf_file):
                print(f"   Warning: {vcf_file} not found")
                continue
            
            print(f"   Loading {os.path.basename(vcf_file)}...")
            batch = []
            file_count = 0
            
            for variant in self.vcf_parser.parse_vcf(vcf_file, limit_per_file):
                batch.append(variant)
                
                if len(batch) >= batch_size:
                    self.repo.batch_create_variants(batch)
                    file_count += len(batch)
                    batch = []
            
            # Insert remaining
            if batch:
                self.repo.batch_create_variants(batch)
                file_count += len(batch)
            
            print(f"      Loaded {file_count:,} variants")
            total_loaded += file_count
        
        return total_loaded
    
    def _load_clinical_data(self):
        """Load clinical data (simulated)"""
        phenotypes = self.clinical_service.get_phenotypes()
        drugs = self.clinical_service.get_drugs()
        
        p_count = self.repo.create_phenotypes(phenotypes)
        d_count = self.repo.create_drugs(drugs)
        
        print(f"   Created {p_count} phenotypes and {d_count} drugs")
    
    def _create_relationships(self):
        """Create all relationships"""
        # Variant CAUSES Phenotype
        causes = self.repo.create_relationships("CAUSES", "Variant", "Phenotype", 1000)
        print(f"   Created {causes} CAUSES relationships")
        
        # Phenotype TREATED_BY Drug
        treatments = self.repo.create_relationships("TREATED_BY", "Phenotype", "Drug", 100)
        print(f"   Created {treatments} TREATED_BY relationships")
        
        # Variant PREDICTS Outcome
        predictions = self.repo.create_relationships("PREDICTS", "Variant", "Outcome", 5000)
        print(f"   Created {predictions} PREDICTS relationships")

        # Drug RESULTS_IN Outcome
        results = self.repo.create_relationships("RESULTS_IN", "Drug", "Outcome", 100)
        print(f"   Created {results} RESULTS_IN relationships")

    def _print_statistics(self, stats: Dict):
        """Print statistics and compliance check"""
        print("\n" + "="*70)
        print(" LAYER 2 COMPLIANCE CHECK")
        print("="*70)
        
        nodes = stats.get('nodes', {})
        relationships = stats.get('relationships', {})
        
        print("\nNodes:")
        for node_type, count in nodes.items():
            print(f"  {node_type}: {count:,}")
        
        print("\nRelationships:")
        for rel_type, count in relationships.items():
            if rel_type != 'total':
                print(f"  {rel_type}: {count:,}")
        
        total = relationships.get('total', 0)
        print(f"\nTotal relationships: {total:,}")
        
        # Check requirements
        meets_edges = total >= self.config.performance['min_graph_edges']
        print(f"\nRequirements:")
        print(f"  Minimum edges ({self.config.performance['min_graph_edges']}): {'✅ PASS' if meets_edges else '❌ FAIL'}")
        print(f"  Target latency: {self.config.performance['target_query_latency_ms']}ms")

# ============================================================================
# LAYER 5: MAIN APPLICATION
# ============================================================================

class VCFToNeo4jLoader:
    """Main application class"""
    
    def __init__(self, config_file='config_simple.toml'):
        self.config = Config(config_file)
        self.repository = Neo4jRepository(
            self.config.neo4j['uri'],
            self.config.neo4j['username'],
            self.config.neo4j['password']
        )
        self.graph_builder = GraphBuilderService(self.repository, self.config)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def find_vcf_files(self) -> List[str]:
        """Find all VCF files in the data directory"""
        vcf_dir = self.config.data['vcf_directory']
        vcf_files = []
        
        if os.path.exists(vcf_dir):
            for file in os.listdir(vcf_dir):
                if file.endswith('.vcf') or file.endswith('.vcf.gz'):
                    vcf_files.append(os.path.join(vcf_dir, file))
        
        return sorted(vcf_files)
    
    def run(self, chromosome: Optional[str] = None, limit: Optional[int] = None):
        """Run the complete pipeline"""
        print("\n🧬 VCF to Neo4j Knowledge Graph Loader")
        print("=" * 50)
        
        # Find VCF files
        vcf_files = self.find_vcf_files()
        
        if chromosome:
            # Filter for specific chromosome
            vcf_files = [f for f in vcf_files if f"chr{chromosome}" in f]
        
        if not vcf_files:
            print("❌ No VCF files found!")
            return
        
        print(f"📁 Found {len(vcf_files)} VCF files")
        
        # Override limit if provided
        if limit:
            self.config.data['max_variants_per_chromosome'] = limit
        
        # Build the graph
        try:
            stats = self.graph_builder.build_graph(
                vcf_files, 
                self.config.data['max_variants_per_chromosome']
            )
            
            print("\n✅ Knowledge graph built successfully!")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.logger.error(f"Pipeline failed: {e}", exc_info=True)
        
        finally:
            self.repository.close()
    
    def query_variant(self, variant_id: str) -> Dict:
        """Query a specific variant"""
        with self.repository.driver.session() as session:
            query = """
                MATCH (v:Variant {variant_id: $variant_id})
                OPTIONAL MATCH (v)-[:CAUSES]->(p:Phenotype)
                OPTIONAL MATCH (p)-[:TREATED_BY]->(d:Drug)
                OPTIONAL MATCH (v)-[:PREDICTS]->(o:Outcome)
                OPTIONAL MATCH (d)-[:RESULTS_IN]->(o2:Outcome)
                RETURN v, collect(DISTINCT p) as phenotypes, 
                       collect(DISTINCT d) as drugs,
                       collect(DISTINCT o) as outcomes
            """
            result = session.run(query, variant_id=variant_id).single()
            
            if result and result['v']:
                return {
                    'variant': dict(result['v']),
                    'phenotypes': [dict(p) for p in result['phenotypes'] if p],
                    'drugs': [dict(d) for d in result['drugs'] if d],
                    'outcomes': [dict(o) for o in result['outcomes'] if o]
                }
            return None
    
    def get_statistics(self) -> Dict:
        """Get current statistics"""
        return self.repository.get_statistics()

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='VCF to Neo4j Knowledge Graph Loader')
    parser.add_argument('--chromosome', help='Specific chromosome to load (e.g., 22)')
    parser.add_argument('--limit', type=int, help='Maximum variants per chromosome')
    parser.add_argument('--query', help='Query a specific variant ID')
    parser.add_argument('--stats', action='store_true', help='Show statistics only')
    
    args = parser.parse_args()
    
    # Initialize loader
    loader = VCFToNeo4jLoader()
    
    if args.query:
        # Query mode
        result = loader.query_variant(args.query)
        if result:
            print(f"\nVariant: {result['variant']}")
            print(f"Phenotypes: {len(result['phenotypes'])}")
            print(f"Drugs: {len(result['drugs'])}")
            print(f"Outcomes: {len(result['outcomes'])}")
        else:
            print(f"Variant {args.query} not found")
    
    elif args.stats:
        # Statistics mode
        stats = loader.get_statistics()
        print("\nDatabase Statistics:")
        print(f"Nodes: {stats.get('nodes', {})}")
        print(f"Relationships: {stats.get('relationships', {})}")
    
    else:
        # Build mode
        loader.run(chromosome=args.chromosome, limit=args.limit)