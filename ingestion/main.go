package main

import (
	"fmt"
	"math/rand"
	"os"

	"github.com/parquet-go/parquet-go"
)

type FiwareAccommodation struct {
	ID               string  `parquet:"id"`
	Name             string  `parquet:"name"`
	Category         string  `parquet:"category"`
	CapacityBeds     int32   `parquet:"capacity_beds"`
	OccupancyRate    float32 `parquet:"occupancy_rate"`
	Latitude         float32 `parquet:"latitude"`
	Longitude        float32 `parquet:"longitude"`
	MunicipalityCode string  `parquet:"municipality_code"`
}

type SegitturDestino struct {
	IDDestino           string  `parquet:"id_destino"`
	DenominacionRecurso string  `parquet:"denominacion_recurso"`
	TipoEspacio         string  `parquet:"tipo_espacio"`
	VisitantesMensuales int32   `parquet:"visitantes_mensuales"`
	GastoMedioDiarioEur float32 `parquet:"gasto_medio_diario_eur"`
	Latitud             float32 `parquet:"latitud"`
	Longitud            float32 `parquet:"longitud"`
	CodigoINEMunicipio  string  `parquet:"codigo_ine_municipio"`
}

type MunicipalityInfo struct {
	Code string
	Name string
	Lat  float32
	Lon  float32
}

var municipalities = []MunicipalityInfo{
	{Code: "17079", Name: "Girona", Lat: 41.9794, Lon: 2.8214},
	{Code: "28079", Name: "Madrid", Lat: 40.4168, Lon: -3.7038},
	{Code: "08019", Name: "Barcelona", Lat: 41.3851, Lon: 2.1734},
	{Code: "41091", Name: "Sevilla", Lat: 37.3891, Lon: -5.9845},
	{Code: "29067", Name: "Málaga", Lat: 36.7213, Lon: -4.4214},
	{Code: "46250", Name: "Valencia", Lat: 39.4699, Lon: -0.3763},
	{Code: "03014", Name: "Alicante", Lat: 38.3452, Lon: -0.4810},
	{Code: "18087", Name: "Granada", Lat: 37.1773, Lon: -3.5986},
	{Code: "07040", Name: "Palma de Mallorca", Lat: 39.5696, Lon: 2.6502},
	{Code: "20069", Name: "Donostia-San Sebastián", Lat: 43.3183, Lon: -1.9812},
	{Code: "38038", Name: "Santa Cruz de Tenerife", Lat: 28.4636, Lon: -16.2518},
	{Code: "35016", Name: "Las Palmas de Gran Canaria", Lat: 28.1235, Lon: -15.4363},
	{Code: "48020", Name: "Bilbao", Lat: 43.2630, Lon: -2.9350},
	{Code: "50297", Name: "Zaragoza", Lat: 41.6488, Lon: -0.8891},
	{Code: "39075", Name: "Santander", Lat: 43.4623, Lon: -3.8099},
}

var fiwareCategories = []string{"Hotel", "Hostal", "Camping", "Apartment"}
var segitturTypes = []string{"AlojamientoHotelero", "ZonaAcampada", "RecursoCultural", "EspacioNatural"}

func generateFiwareData(count int) []FiwareAccommodation {
	r := rand.New(rand.NewSource(42))
	var data []FiwareAccommodation
	for i := 1; i <= count; i++ {
		m := municipalities[r.Intn(len(municipalities))]
		cat := fiwareCategories[r.Intn(len(fiwareCategories))]
		beds := int32(20 + r.Intn(480))
		occupancy := float32(0.40 + r.Float64()*0.55)
		// Small jitter in lat/lon
		lat := m.Lat + float32((r.Float64()-0.5)*0.04)
		lon := m.Lon + float32((r.Float64()-0.5)*0.04)
		name := fmt.Sprintf("%s %s %d", cat, m.Name, i)

		data = append(data, FiwareAccommodation{
			ID:               fmt.Sprintf("urn:ngsi-ld:Accommodation:ES:%s:%04d", m.Code, i),
			Name:             name,
			Category:         cat,
			CapacityBeds:     beds,
			OccupancyRate:    float32(int(occupancy*100)) / 100.0,
			Latitude:         lat,
			Longitude:        lon,
			MunicipalityCode: m.Code,
		})
	}
	return data
}

func generateSegitturData(count int) []SegitturDestino {
	r := rand.New(rand.NewSource(1337))
	var data []SegitturDestino
	for i := 1; i <= count; i++ {
		m := municipalities[r.Intn(len(municipalities))]
		tipo := segitturTypes[r.Intn(len(segitturTypes))]
		visitors := int32(800 + r.Intn(35000))
		spend := float32(45.0 + r.Float64()*185.0)
		lat := m.Lat + float32((r.Float64()-0.5)*0.04)
		lon := m.Lon + float32((r.Float64()-0.5)*0.04)
		name := fmt.Sprintf("Recurso %s %s #%d", tipo, m.Name, i)

		data = append(data, SegitturDestino{
			IDDestino:           fmt.Sprintf("SEGITTUR-POI-%s-%04d", m.Code, i),
			DenominacionRecurso: name,
			TipoEspacio:         tipo,
			VisitantesMensuales: visitors,
			GastoMedioDiarioEur: float32(int(spend*100)) / 100.0,
			Latitud:             lat,
			Longitud:            lon,
			CodigoINEMunicipio:  m.Code,
		})
	}
	return data
}

func main() {
	outDir := "/tmp/raw_parquet"
	if len(os.Args) > 1 {
		outDir = os.Args[1]
	}
	if err := os.MkdirAll(outDir, 0755); err != nil {
		panic(err)
	}

	fiwareRecords := generateFiwareData(80)
	segitturRecords := generateSegitturData(80)

	fiwarePath := fmt.Sprintf("%s/fiware_accommodations.parquet", outDir)
	segitturPath := fmt.Sprintf("%s/segittur_destinos.parquet", outDir)

	fmt.Printf("[data-generator] Writing %d FIWARE records to %s via parquet-go...\n", len(fiwareRecords), fiwarePath)
	if err := parquet.WriteFile(fiwarePath, fiwareRecords); err != nil {
		panic(err)
	}

	fmt.Printf("[data-generator] Writing %d SEGITTUR records to %s via parquet-go...\n", len(segitturRecords), segitturPath)
	if err := parquet.WriteFile(segitturPath, segitturRecords); err != nil {
		panic(err)
	}

	fmt.Println("[data-generator] Parquet generation completed successfully!")
}
