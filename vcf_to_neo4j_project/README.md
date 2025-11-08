# VCF to Neo4j Knowledge Graph - Layered Architecture

A clean, modular implementation of the VCF to Neo4j pipeline with proper separation of concerns.

## 📁 Project Structure

```
vcf_to_neo4j/
├── geneData/                    # VCF data files
│   └── ALL.chr*.vcf(.gz)       # 1000 Genomes files
├── genv/                        # Python virtual environment
├── config.toml                  # Configuration file
├── vcf_to_neo4j_layered.py    # Main layered application
└── README.md                    # This file
```

## 🏗️ Architecture Layers

The code is organized into 5 clean layers:

### Layer 1: Configuration
- Loads settings from `config.toml`
- Manages all configuration parameters

### Layer 2: Models (Domain Objects)
- `Variant` - Genomic variant entity
- `Phenotype` - Disease/condition entity  
- `Drug` - Medication entity
- Pure data structures with validation

### Layer 3: Data Access (Repository)
- `Neo4jRepository` - All database operations
- Handles connections, queries, indexes
- Repository pattern for clean data access

### Layer 4: Services (Business Logic)
- `VCFParserService` - Parses VCF files
- `ClinicalDataService` - Manages clinical data
- `GraphBuilderService` - Orchestrates graph construction
- Business logic separated from data access

### Layer 5: Application
- `VCFToNeo4jLoader` - Main application class
- Command-line interface
- Coordinates all layers

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Activate virtual environment
source genv/bin/activate

# Install dependencies
pip install neo4j cyvcf2 toml
```

### 2. Configure Neo4j

Edit `config.toml`:
```toml
[neo4j]
username = "neo4j"
password = "genegenius"
```

### 3. Run the Loader

```bash
# Load all VCF files with 5000 variants per chromosome
python vcf_to_neo4j_layered.py --limit 5000

# Load specific chromosome
python vcf_to_neo4j_layered.py --chromosome 22 --limit 5000

# Load everything (no limit)
python vcf_to_neo4j_layered.py
```

## 💻 Usage Examples

### Build Knowledge Graph
```bash
python vcf_to_neo4j_layered.py --limit 5000
```

### Query a Variant
```bash
python vcf_to_neo4j_layered.py --query "22:16050075:A:G"
```

### Show Statistics
```bash
python vcf_to_neo4j_layered.py --stats
```

## 📊 Graph Schema

The pipeline creates this Layer 2 compliant schema:

```
Nodes:
- Variant (from VCF files)
- Phenotype (simulated clinical data)
- Drug (FDA medications)
- Outcome (predictions)

Relationships:
- (Variant)-[:CAUSES]->(Phenotype)
- (Phenotype)-[:TREATED_BY]->(Drug)
- (Variant)-[:PREDICTS]->(Outcome)
```

## ⚙️ Configuration

All settings in `config.toml`:

```toml
[neo4j]
uri = "bolt://localhost:7687"
username = "neo4j"
password = "password123"

[data]
vcf_directory = "geneData"
batch_size = 1000
max_variants_per_chromosome = 5000

[performance]
target_query_latency_ms = 100
min_graph_edges = 3000
```

## 🔄 Data Flow

1. **Configuration** loaded from `config.toml`
2. **VCF files** parsed by `VCFParserService`
3. **Variants** created via `Neo4jRepository`
4. **Clinical data** added by `ClinicalDataService`
5. **Relationships** built by `GraphBuilderService`
6. **Statistics** verified against requirements

## 📈 Performance

- Batch processing: 1000 variants at a time
- Indexed queries: <100ms latency
- Supports millions of variants
- Memory efficient streaming

## ✅ Layer 2 Compliance

The system verifies:
- ✅ Minimum 3000 graph edges
- ✅ Query latency <100ms
- ✅ Required relationship types
- ✅ Proper graph schema

## 🎯 Key Benefits of Layered Architecture

1. **Separation of Concerns** - Each layer has one responsibility
2. **Testability** - Each layer can be tested independently
3. **Maintainability** - Easy to understand and modify
4. **Reusability** - Services can be reused
5. **Scalability** - Can add features without breaking existing code

## 📝 Notes

- Currently uses **simulated clinical data**
- Real ClinVar/PharmGKB integration can be added to `ClinicalDataService`
- Supports both cyvcf2 and pysam parsers
- All configuration externalized to `config.toml`

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Import error | Install: `pip install neo4j cyvcf2 toml` |
| Neo4j connection | Check credentials in `config.toml` |
| No VCF files | Ensure files in `geneData/` directory |
| Memory issues | Reduce `max_variants_per_chromosome` |

## 📄 License

Proprietary - GeneGenius Inc.