package main

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

func main() {
	router := gin.Default()

	router.GET("/map-data", func(c *gin.Context) {
		mapData := map[string]interface{}{
			"data": []interface{}{
				map[string]interface{}{
					"type":              "choropleth",
					"locations":         []string{"USA", "Canada", "Mexico"},
					"z":                 []int{10, 15, 20},
					"text":              []string{"USA", "Canada", "Mexico"},
					"colorscale":        "Viridis",
					"autocolorscale":    false,
					"marker_line_color": "darkgray",
					"marker_line_width": 0.5,
					"colorbar_title":    "Value",
				},
			},
			"layout": map[string]interface{}{
				"title": "World Map",
				"geo": map[string]interface{}{
					"showframe":       false,
					"showcoastlines":  false,
					"projection_type": "equirectangular",
				},
			},
		}

		c.JSON(http.StatusOK, mapData)
	})

	router.Run(":8000")
}
